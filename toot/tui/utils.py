import re

from datetime import datetime

HASHTAG_PATTERN = re.compile(r'(?<!\w)(#\w+)\b')


def parse_datetime(value):
    """Returns an aware datetime in local timezone"""
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z").astimezone()


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


def highlight_hashtags(line, attr="hashtag"):
    return [
        (attr, p) if p.startswith("#") else p
        for p in re.split(HASHTAG_PATTERN, line)
    ]
