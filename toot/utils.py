# -*- coding: utf-8 -*-

import os
import re
import socket
import unicodedata
import warnings

from bs4 import BeautifulSoup
from wcwidth import wcwidth, wcswidth

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


def trunc(text, length):
    """
    Truncates text to given length, taking into account wide characters.

    If truncated, the last char is replaced by an elipsis.
    """
    if length < 1:
        raise ValueError("length should be 1 or larger")

    # Remove whitespace first so no unneccesary truncation is done.
    text = text.strip()
    text_length = wcswidth(text)

    if text_length <= length:
        return text

    # We cannot just remove n characters from the end since we don't know how
    # wide these characters are and how it will affect text length.
    # Use wcwidth to determine how many characters need to be truncated.
    chars_to_truncate = 0
    trunc_length = 0
    for char in reversed(text):
        chars_to_truncate += 1
        trunc_length += wcwidth(char)
        if text_length - trunc_length <= length:
            break

    # Additional char to make room for elipsis
    n = chars_to_truncate + 1
    return text[:-n].strip() + '…'


def pad(text, length):
    """Pads text to given length, taking into account wide characters."""
    text_length = wcswidth(text)

    if text_length < length:
        return text + ' ' * (length - text_length)

    return text


def fit_text(text, length):
    """Makes text fit the given length by padding or truncating it."""
    text_length = wcswidth(text)

    if text_length > length:
        return trunc(text, length)

    if text_length < length:
        return pad(text, length)

    return text


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
