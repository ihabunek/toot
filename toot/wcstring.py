"""
Utilities for dealing with string containing wide characters.
"""

import re

from wcwidth import wcwidth, wcswidth


def _wc_hard_wrap(line, length):
    """
    Wrap text to length characters, breaking when target length is reached,
    taking into account character width.

    Used to wrap lines which cannot be wrapped on whitespace.
    """
    chars = []
    chars_len = 0
    for char in line:
        char_len = wcwidth(char)
        if chars_len + char_len > length:
            yield "".join(chars)
            chars = []
            chars_len = 0

        chars.append(char)
        chars_len += char_len

    if chars:
        yield "".join(chars)


def wc_wrap(text, length):
    """
    Wrap text to given length, breaking on whitespace and taking into account
    character width.

    Meant for use on a single line or paragraph. Will destroy spacing between
    words and paragraphs and any indentation.
    """
    line_words = []
    line_len = 0

    words = re.split(r"\s+", text.strip())
    for word in words:
        word_len = wcswidth(word)

        if line_words and line_len + word_len > length:
            line = " ".join(line_words)
            if line_len <= length:
                yield line
            else:
                yield from _wc_hard_wrap(line, length)

            line_words = []
            line_len = 0

        line_words.append(word)
        line_len += word_len + 1  # add 1 to account for space between words

    if line_words:
        line = " ".join(line_words)
        if line_len <= length:
            yield line
        else:
            yield from _wc_hard_wrap(line, length)
