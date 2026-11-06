"""
Utilities for dealing with string containing wide characters.
"""

import re
from typing import Generator, List

from wcwidth import iter_graphemes, iter_graphemes_reverse, wcswidth


def _wc_hard_wrap(line: str, length: int) -> Generator[str, None, None]:
    """
    Wrap text to length characters, breaking when target length is reached,
    taking into account character width.

    Used to wrap lines which cannot be wrapped on whitespace.

    Steps a grapheme cluster at a time, since a cluster is what a terminal
    draws as one character and may be several code points: a flag, an emoji
    carrying a skin tone, a family joined by zero-width joiners.
    """
    chars = []
    chars_len = 0
    for char in iter_graphemes(line):
        char_len = wcswidth(char)
        if chars_len + char_len > length:
            yield "".join(chars)
            chars: List[str] = []
            chars_len = 0

        chars.append(char)
        chars_len += char_len

    if chars:
        yield "".join(chars)


def wc_wrap(text: str, length: int) -> Generator[str, None, None]:
    """
    Wrap text to given length, breaking on whitespace and taking into account
    character width.

    Meant for use on a single line or paragraph. Will destroy spacing between
    words and paragraphs and any indentation.
    """
    line_words: List[str] = []
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


def trunc(text: str, length: int) -> str:
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
    # wide these characters are and how it will affect text length. Walk back
    # a grapheme cluster at a time, asking wcswidth for each, so the cut lands
    # between glyphs rather than inside one: a family emoji is four code
    # points joined by zero-width joiners and is two columns wide, and cutting
    # it short leaves a dangling joiner behind. The extra column is the room
    # the ellipsis needs.
    remaining = text_length
    cut = len(text)
    for cluster in iter_graphemes_reverse(text):
        cut -= len(cluster)
        remaining -= wcswidth(cluster)
        if remaining + 1 <= length:
            break

    return text[:cut].strip() + '…'


def pad(text: str, length: int) -> str:
    """Pads text to given length, taking into account wide characters."""
    text_length = wcswidth(text)

    if text_length < length:
        return text + ' ' * (length - text_length)

    return text


def fit_text(text: str, length: int) -> str:
    """Makes text fit the given length by padding or truncating it."""
    text_length = wcswidth(text)

    if text_length > length:
        return trunc(text, length)

    if text_length < length:
        return pad(text, length)

    return text
