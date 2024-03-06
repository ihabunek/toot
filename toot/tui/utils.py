import base64
import re
import urwid

from functools import reduce
from html.parser import HTMLParser
from typing import List

HASHTAG_PATTERN = re.compile(r'(?<!\w)(#\w+)\b')


def highlight_keys(text, high_attr, low_attr=""):
    """
    Takes a string and adds high_attr attribute to parts in square brackets,
    and optionally low_attr attribute to parts outside square brackets.

    The result can be rendered using a urwid.Text widget.

    For example:

    >>> highlight_keys("[P]rint [V]iew", "blue")
    >>> [('blue', 'P'), 'rint ', ('blue', 'V'), 'iew']
    """
    def _gen():
        highlighted = False
        for part in re.split("\\[|\\]", text):
            if part:
                if highlighted:
                    yield (high_attr, part) if high_attr else part
                else:
                    yield (low_attr, part) if low_attr else part
            highlighted = not highlighted
    return list(_gen())


def highlight_hashtags(line):
    hline = []

    for p in re.split(HASHTAG_PATTERN, line):
        if p.startswith("#"):
            hline.append(("hashtag", p))
        else:
            hline.append(p)

    return hline


class LinkParser(HTMLParser):
    def reset(self):
        super().reset()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href, title = None, None
            for name, value in attrs:
                if name == "href":
                    href = value
                if name == "title":
                    title = value
            if href:
                self.links.append((href, title))


def parse_content_links(content):
    """Parse <a> tags from status's `content` and return them as a list of
    (href, title), where `title` may be None.
    """
    parser = LinkParser()
    parser.feed(content)
    return parser.links[:]


def copy_to_clipboard(screen: urwid.raw_display.Screen, text: str):
    """ copy text to clipboard using OSC 52
    This escape sequence is documented
    here https://iterm2.com/documentation-escape-codes.html
    It has wide support - XTerm, Windows Terminal,
    Kitty, iTerm2, others. Some terminals may require a setting to be
    enabled in order to use OSC 52 clipboard functions.
    """

    text_bytes = text.encode("utf-8")
    b64_bytes = base64.b64encode(text_bytes)
    b64_text = b64_bytes.decode("utf-8")

    screen.write(f"\033]52;c;{b64_text}\a")
    screen.flush()


def get_max_toot_chars(instance, default=500):
    # Mastodon
    # https://docs.joinmastodon.org/entities/Instance/#max_characters
    max_toot_chars = deep_get(instance, ["configuration", "statuses", "max_characters"])
    if isinstance(max_toot_chars, int):
        return max_toot_chars

    # Pleroma
    max_toot_chars = instance.get("max_toot_chars")
    if isinstance(max_toot_chars, int):
        return max_toot_chars

    return default


def deep_get(adict: dict, path: List[str], default=None):
    return reduce(
        lambda d, key: d.get(key, default) if isinstance(d, dict) else default,
        path,
        adict
    )
