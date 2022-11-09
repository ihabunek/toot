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


def trunc(text, length):
    """
    Truncates text to given length, taking into account wide characters.

    If truncated, the last char is replaced by an ellipsis.
    """
    if length < 1:
        raise ValueError("length should be 1 or larger")

    # Remove whitespace first so no unnecessary truncation is done.
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

    # Additional char to make room for ellipsis
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
