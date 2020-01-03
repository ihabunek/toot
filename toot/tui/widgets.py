import urwid


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
