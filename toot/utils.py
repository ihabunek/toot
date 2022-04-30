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


EDITOR_INPUT_INSTRUCTIONS = """
# Please enter your toot. Lines starting with '#' will be ignored, and an empty
# message aborts the post. Metadata comments can be set for media, description, lang, spoiler
"""

def parse_editor_meta(line, args):
    """Parse a comment metadata line in the editor box. Returns false if the line is a text line"""
    if not line.startswith('#'):
        return False
    line = line.lstrip('# \t')
    key, sep, val = line.partition(':')
    key = key.strip()
    val = val.strip()
    if sep == '' or val == '':
        return True
    # TODO override user with 'from'
    if key == 'media':
        args.media = args.media or []
        args.media.append(val)
    elif key == 'description':
        args.description = args.description or []
        args.description.append(val)
    elif key == 'lang' or key == 'language':
        args.language = val
    elif key == 'spoiler':
        args.spoiler_text = val
    else:
        print_out("Ignoring unsupported comment metadata <red>{}</red> with value <yellow>{}</yellow>.".format(key, val))
    return True


def parse_editor_input(args):
    editor = args.editor
    """Lets user input text using an editor."""
    initial_text = (args.text or "") + EDITOR_INPUT_INSTRUCTIONS

    with tempfile.NamedTemporaryFile() as f:
        f.write(initial_text.encode())
        f.flush()

        subprocess.run([editor, f.name])

        f.seek(0)
        text = f.read().decode()

    lines = text.strip().splitlines()
    lines = (l for l in lines if not parse_editor_meta(l, args))
    args.text = "\n".join(lines)
    return args
