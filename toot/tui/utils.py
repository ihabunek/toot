from html.parser import HTMLParser
import os
import re
import shutil
import subprocess

from datetime import datetime, timezone

HASHTAG_PATTERN = re.compile(r'(?<!\w)(#\w+)\b')


def parse_datetime(value):
    """Returns an aware datetime in local timezone"""

    # In Python < 3.7, `%z` does not match `Z` offset
    # https://docs.python.org/3.7/library/datetime.html#strftime-and-strptime-behavior
    if value.endswith("Z"):
        dttm = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    else:
        dttm = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")

    # When running tests return datetime in UTC so that tests don't depend on
    # the local timezone
    if "PYTEST_CURRENT_TEST" in os.environ:
        return dttm.astimezone(timezone.utc)

    return dttm.astimezone()


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


def show_media(paths):
    """
    Attempt to open an image viewer to show given media files.

    FIXME: This is not very thought out, but works for me.
    Once settings are implemented, add an option for the user to configure their
    prefered media viewer.
    """
    viewer = None
    potential_viewers = [
        "feh",
        "eog",
        "display"
    ]
    for v in potential_viewers:
        viewer = shutil.which(v)
        if viewer:
            break

    if not viewer:
        raise Exception("Cannot find an image viewer")

    subprocess.run([viewer] + paths)


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
