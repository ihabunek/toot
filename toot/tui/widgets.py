from typing import List
import urwid
import re
import requests
from PIL import Image
from term_image.image import AutoImage
from term_image.widget import UrwidImage
from .utils import can_render_pixels


class Clickable:
    """
    Add a `click` signal which is sent when the item is activated or clicked.

    TODO: make it work on widgets which have other signals.
    """
    signals = ["click"]

    def keypress(self, size, key):
        if self._command_map[key] == urwid.ACTIVATE:
            self._emit('click')
            return

        return key

    def mouse_event(self, size, event, button, x, y, focus):
        if button == 1:
            self._emit('click')


class SelectableText(Clickable, urwid.Text):
    _selectable = True


class SelectableColumns(Clickable, urwid.Columns):
    _selectable = True


class EditBox(urwid.AttrWrap):
    """Styled edit box."""
    def __init__(self, *args, **kwargs):
        self.edit = urwid.Edit(*args, **kwargs)
        return super().__init__(self.edit, "editbox", "editbox_focused")


class Button(urwid.AttrWrap):
    """Styled button."""
    def __init__(self, *args, **kwargs):
        button = urwid.Button(*args, **kwargs)
        padding = urwid.Padding(button, width=len(args[0]) + 4)
        return super().__init__(padding, "button", "button_focused")

    def set_label(self, *args, **kwargs):
        self.original_widget.original_widget.set_label(*args, **kwargs)
        self.original_widget.width = len(args[0]) + 4


class CheckBox(urwid.AttrWrap):
    """Styled checkbox."""
    def __init__(self, *args, **kwargs):
        self.button = urwid.CheckBox(*args, **kwargs)
        padding = urwid.Padding(self.button, width=len(args[0]) + 4)
        return super().__init__(padding, "button", "button_focused")

    def get_state(self):
        """Return the state of the checkbox."""
        return self.button._state


class RadioButton(urwid.AttrWrap):
    """Styled radiobutton."""
    def __init__(self, *args, **kwargs):
        button = urwid.RadioButton(*args, **kwargs)
        padding = urwid.Padding(button, width=len(args[1]) + 4)
        return super().__init__(padding, "button", "button_focused")


class EmojiText(urwid.Padding):
    """Widget to render text with embedded custom emojis

    Note, these are Mastodon custom server emojis
    which are indicated by :shortcode: in the text
    and rendered as images on supporting clients.

    For clients that do not support pixel rendering,
    they are rendered as plain text :shortcode:

    This widget was designed for use with displaynames
    but could be used with any string of text.
    However, due to the internal use of columns,
    this widget will not wrap multi-line text
    correctly.

    Note, you can embed this widget in AttrWrap to style
    the text as desired.

    Parameters:

    text -- text string (with or without embedded shortcodes)
    emojis -- list of emojis with nested lists of associated
    shortcodes and URLs
    """
    image_cache = {}

    def __init__(self, text: str, emojis: List):
        columns = []

        if not can_render_pixels():
            return self.plain(text, columns)

        # build a regex to find all available shortcodes
        regex = '|'.join(f':{emoji["shortcode"]}:' for emoji in emojis)

        if 0 == len(regex):
            # if no shortcodes, just output plain Text
            return self.plain(text, columns)

        regex = f"({regex})"

        for word in re.split(regex, text):
            if word.startswith(":") and word.endswith(":"):
                shortcode = word[1:-1]
                found = False
                for emoji in emojis:
                    if emoji["shortcode"] == shortcode:
                        try:
                            img = EmojiText.image_cache.get(str(hash(emoji["url"])))
                            if not img:
                                # TODO: consider asynchronous loading in future
                                img = Image.open(requests.get(emoji["url"], stream=True).raw)
                                EmojiText.image_cache[str(hash(emoji["url"]))] = img
                            image_widget = urwid.BoxAdapter(UrwidImage(AutoImage(img), upscale=True), 1)
                            columns.append(image_widget)
                        except Exception:
                            columns.append(("pack", urwid.Text(word)))
                        finally:
                            found = True
                            break
                if found is False:
                    columns.append(("pack", urwid.Text(word)))
            else:
                columns.append(("pack", urwid.Text(word)))

        columns.append(("weight", 9999, urwid.Text("")))

        column_widget = urwid.Columns(columns, dividechars=0, min_width=2)
        super().__init__(column_widget)

    def plain(self, text, columns):
        # if can't render pixels, just output plain Text
        columns.append(("pack", urwid.Text(text)))
        columns.append(("weight", 9999, urwid.Text("")))
        column_widget = urwid.Columns(columns, dividechars=1, min_width=2)
        super().__init__(column_widget)
