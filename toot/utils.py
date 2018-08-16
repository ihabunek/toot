# -*- coding: utf-8 -*-

import re
import socket
import unicodedata

from bs4 import BeautifulSoup

from toot.exceptions import ConsoleError


def get_text(html):
    """Converts html to text, strips all tags."""
    text = BeautifulSoup(html, "html.parser").get_text()
    text = re.sub('&apos;*', "'", text)

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


def trunc(text, length):
    """Trims text to given length, if trimmed appends ellipsis."""
    if len(text) <= length:
        return text

    return text[:length - 1] + '…'
