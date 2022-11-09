# -*- coding: utf-8 -*-

import os
import re
import socket
import subprocess
import tempfile
import unicodedata
import warnings

from bs4 import BeautifulSoup

from toot.exceptions import ConsoleError

from argparse import FileType

VISIBILITY_CHOICES = ['public', 'unlisted', 'private', 'direct']

def language(value):
    """Validates the language parameter"""
    if len(value) != 3:
        raise ArgumentTypeError(
            "Invalid language specified: '{}'. Expected a 3 letter "
            "abbreviation according to ISO 639-2 standard.".format(value)
        )

    return value

def visibility(value):
    """Validates the visibility parameter"""
    if value not in VISIBILITY_CHOICES:
        raise ValueError("Invalid visibility value")

    return value

def visibility_choices():
    return ", ".join(VISIBILITY_CHOICES)

def str_bool(b):
    """Convert boolean to string, in the way expected by the API."""
    return "true" if b else "false"


def get_text(html):
    """Converts html to text, strips all tags."""

    # Ignore warnings made by BeautifulSoup, if passed something that looks like
    # a file (e.g. a dot which matches current dict), it will warn that the file
    # should be opened instead of passing a filename.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        text = BeautifulSoup(html.replace('&apos;', "'"), "html.parser").get_text()

    return unicodedata.normalize('NFKC', text)


def parse_html(html):
    """Attempt to convert html to plain text while keeping line breaks.
    Returns a list of paragraphs, each being a list of lines.
    """
    paragraphs = re.split("</?p[^>]*>", html)

    # Convert <br>s to line breaks and remove empty paragraphs
    paragraphs = [re.split("<br */?>", p) for p in paragraphs if p]

    # Convert each line in each paragraph to plain text:
    return [[get_text(l) for l in p] for p in paragraphs]


def format_content(content):
    """Given a Status contents in HTML, converts it into lines of plain text.

    Returns a generator yielding lines of content.
    """

    paragraphs = parse_html(content)

    first = True

    for paragraph in paragraphs:
        if not first:
            yield ""

        for line in paragraph:
            yield line

        first = False


def domain_exists(name):
    try:
        socket.gethostbyname(name)
        return True
    except OSError:
        return False


def assert_domain_exists(domain):
    if not domain_exists(domain):
        raise ConsoleError("Domain {} not found".format(domain))


EOF_KEY = "Ctrl-Z" if os.name == 'nt' else "Ctrl-D"


def multiline_input():
    """Lets user input multiple lines of text, terminated by EOF."""
    lines = []
    while True:
        try:
            lines.append(input())
        except EOFError:
            break

    return "\n".join(lines).strip()


EDITOR_INPUT_INSTRUCTIONS = """--
help: Please enter your toot. An empty message aborts the post.
help: This initial block between -- will be ignored.
help: Metadata can be added in this block in key: value form.
help: Supported keys are: from, media, description, lang, spoiler, reply-to, visibility, sensitive
"""

def parse_editor_meta(line, args):
    """Parse a metadata line in the editor box."""
    key, sep, val = line.partition(':')
    key = key.strip().lower()
    val = val.strip()
    if key == 'help'  or sep == '' or val == '':
        return True
    if key in ['from', 'using']:
        args.using = val
    elif key == 'media':
        args.media.append(FileType('rb')(val))
    elif key == 'description':
        args.description.append(val)
    elif key in ['lang', 'language']:
        args.language = language(val)
    elif key in ['spoiler', 'spoiler-text', 'spoiler_text']:
        args.spoiler_text = val
    elif key in ['reply-to', 'reply_to', 'replyto', 'in-reply-to', 'in_reply_to']:
        args.reply_to = val
    elif key == 'visibility':
        args.visibility = visibility(val)
    elif key in ['sensitive', 'nsfw']:
        # 0, f, false, n, no will count as not-sensitive, any other value will be taken as a yes
        args.sensitive = val.lower() not in [ '0', 'f', 'false', 'n', 'no' ]
    else:
        print_out("Ignoring unsupported metadata <red>{}</red> with value <yellow>{}</yellow>.".format(key, val))
        return False
    return True

def parse_editor_input(args):
    """Lets user input text using an editor."""

    editor = args.editor
    # initialize metacomments from the args field, and reset them in args so that
    # they get reset if removed from the metacomments
    meta = ""
    if args.using:
        meta += "from: " + args.using + "\n"
    if args.reply_to:
        meta += "reply_to: " + args.reply_to + "\n"
        args.reply_to = None
    if args.visibility:
        meta += "visibility: " + args.visibility + "\n"
        args.visibility = 'public' # TODO can we take the default from the command definition?
    if args.language:
        meta += "lang: " + args.language + "\n"
        args.language = None
    if args.spoiler_text:
        meta += "spoiler: " + args.spoiler_text + "\n"
        args.spoiler_text = None
    if args.sensitive:
        meta += "sensitive: " + args.sensitive + "\n"
        args.sensitive = False

    media = args.media or []
    descriptions = args.description or []
    if len(media) > 0:
        for idx, file in enumerate(media):
            meta += "media: " + file.name + "\n"
            # encourage the user to add descriptions, always present the meta field
            desc = descriptions[idx].strip() if idx < len(descriptions) else ''
            meta += "description: " + desc + "\n"
    if len(descriptions) > len(media):
        for idx, desc in enumerate(descriptions):
            if idx < len(media):
                continue
            meta += "description: "+ descriptions[idx].strip() + "\n"

    args.media = []
    args.description = []
    text = "{}{}--\n{}".format(EDITOR_INPUT_INSTRUCTIONS, meta, (args.text or ""))

    prev_using = args.using

    # loop to avoid losing text if something goes wrong (e.g. wrong visibility setting)
    with tempfile.NamedTemporaryFile() as f:
        while True:
            try:
                f.seek(0)
                f.write(text.encode())
                f.flush()

                subprocess.run([editor, f.name])

                f.seek(0)
                text = f.read().decode()

                chunks = text.split("--\n", 3)
                pre = ''
                meta = ''
                toot = ''

                try:
                    pre, meta, toot = chunks
                except ValueError:
                    toot = text

                # pre should be empty
                if pre:
                    raise ValueError("metadata block offset")

                for l in meta.splitlines():
                    parse_editor_meta(l, args)
                args.text = toot.strip()

                # sanity check: this wll be checked by post() too, but we want to catch this early so that
                # the user can still fix things in the editor
                if args.media and len(args.media) > 4:
                    raise ConsoleError("Cannot attach more than 4 files.")

                # if the user specified a different account, we check if it is valid here,
                # so that the message is not lost in case of errors
                # TODO FIXME this way of doing things is leading to a lot of duplicate code,
                # the whole system should be refactored so that this error handling (with the retry)
                # is handled at a higher level
                if args.using != prev_using:
                    user, app = config.get_user_app(parsed_args.using)
                    if not user or not app:
                        raise ConsoleError("User '{}' not found".format(parsed_args.using))
            except Exception as e:
                if len(text) < 3:
                    text = "--\nerror: {}\n--\n{}".format(str(e), text)
                else:
                    text = text[:3] + "error: {}\n".format(str(e)) + text[3:]
                continue
            break

    return args
