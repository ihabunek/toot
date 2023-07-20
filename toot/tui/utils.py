import base64
import re
import shutil
import subprocess
import sys
import urwid
import math
from collections import OrderedDict
from functools import reduce
from html.parser import HTMLParser
from typing import List

from PIL import Image, ImageDraw
from .images import GraphicsImage, auto_image_class

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


def highlight_hashtags(line, followed_tags, attr="hashtag", followed_attr="hashtag_followed"):
    hline = []

    for p in re.split(HASHTAG_PATTERN, line):
        if p.startswith("#"):
            if p[1:].lower() in (t.lower() for t in followed_tags):
                hline.append((followed_attr, p))
            else:
                hline.append((attr, p))
        else:
            hline.append(p)

    return hline


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


def resize_image(basewidth: int, baseheight: int, img: Image.Image) -> Image.Image:
    if baseheight and not basewidth:
        hpercent = baseheight / float(img.size[1])
        width = math.ceil(img.size[0] * hpercent)
        img = img.resize((width, baseheight), Image.Resampling.LANCZOS)
    elif basewidth and not baseheight:
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((basewidth, hsize), Image.Resampling.LANCZOS)
    else:
        img = img.resize((basewidth, baseheight), Image.Resampling.LANCZOS)

    if img.mode != 'P':
        img = img.convert('RGB')
    return img


def add_corners(img, rad):
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new('L', img.size, "white")
    w, h = img.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    img.putalpha(alpha)
    return img


def can_render_pixels():
    # subclasses of GraphicsImage render to pixels
    return issubclass(auto_image_class(), GraphicsImage)


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


class ImageCache(OrderedDict):
    """Dict with a limited size, ejecting LRUs as needed.
        Default max size = 10Mb"""

    def __init__(self, *args, cache_max_bytes: int = 1024 * 1024 * 10, **kwargs):
        assert cache_max_bytes > 0
        self.total_value_size = 0
        self.cache_max_bytes = cache_max_bytes

        super().__init__(*args, **kwargs)

    def __setitem__(self, key: str, value: Image.Image):
        if key in self:
            self.total_value_size -= sys.getsizeof(super().__getitem__(key).tobytes())
        self.total_value_size += sys.getsizeof(value.tobytes())
        super().__setitem__(key, value)
        super().move_to_end(key)

        while self.total_value_size > self.cache_max_bytes:
            old_key, value = next(iter(self.items()))
            sz = sys.getsizeof(value.tobytes())
            super().__delitem__(old_key)
            self.total_value_size -= sz

    def __getitem__(self, key: str):
        val = super().__getitem__(key)
        super().move_to_end(key)
        return val
