__all__ = ("Hyperlink",)

import urwid


class Hyperlink(urwid.WidgetWrap):
    def __init__(
        self,
        uri,
        attr,
        text,
    ):
        pass

    def render(self, size, focus):
        return None


class HyperlinkCanvas(urwid.Canvas):
    def __init__(self, uri: str, text_canv: urwid.TextCanvas):
        pass

    def cols(self):
        return 0

    def content(self, *args, **kwargs):
        yield [None]

    def rows(self):
        return 0
