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


EDITOR_DIVIDER = "------------------------ >8 ------------------------"

EDITOR_INPUT_INSTRUCTIONS = f"""
{EDITOR_DIVIDER}
Do not modify or remove the line above.
Enter your toot above it.
Everything below it will be ignored.
"""


def editor_input(editor, initial_text):
    """Lets user input text using an editor."""
    initial_text = (initial_text or "") + EDITOR_INPUT_INSTRUCTIONS

    with tempfile.NamedTemporaryFile(suffix='.toot') as f:
        f.write(initial_text.encode())
        f.flush()

        subprocess.run([editor, f.name])

        f.seek(0)
        text = f.read().decode()

    return text.split(EDITOR_DIVIDER)[0].strip()
