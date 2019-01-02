# -*- coding: utf-8 -*-

import os
import re
import socket
import unicodedata

from bs4 import BeautifulSoup
from wcwidth import wcswidth

from toot.exceptions import ConsoleError


def get_text(html):
    """Converts html to text, strips all tags."""
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


def trunc(text, length, text_length=None):
    """Trims text to given length, if trimmed appends ellipsis."""
    if text_length is None:
        text_length = len(text)
    if text_length <= length:
        return text

    return text[:length - 1] + '…'


def pad(text, length, fill=' '):
    text_length = wcswidth(text)
    text = trunc(text, length, text_length)
    assert len(text) <= length
    return text + fill * (length - text_length)


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
