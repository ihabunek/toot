import urwid
from wcwidth import wcswidth


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
        padding = urwid.Padding(button, width=wcswidth(args[0]) + 4)
        return super().__init__(padding, "button", "button_focused")

    def set_label(self, *args, **kwargs):
        self.original_widget.original_widget.set_label(*args, **kwargs)
        self.original_widget.width = wcswidth(args[0]) + 4


class CheckBox(urwid.AttrWrap):
    """Styled checkbox."""
    def __init__(self, *args, **kwargs):
        self.button = urwid.CheckBox(*args, **kwargs)
        padding = urwid.Padding(self.button, width=len(args[0]) + 4)
        return super().__init__(padding, "button", "button_focused")

    def get_state(self):
        """Return the state of the checkbox."""
        return self.button.get_state()


class RadioButton(urwid.AttrWrap):
    """Styled radiobutton."""
    def __init__(self, *args, **kwargs):
        button = urwid.RadioButton(*args, **kwargs)
        padding = urwid.Padding(button, width=len(args[1]) + 4)
        return super().__init__(padding, "button", "button_focused")


class ModalBox(urwid.Frame):
    def __init__(self, message):
        text = urwid.Text(message)
        filler = urwid.Filler(text, valign='top', top=1, bottom=1)
        padding = urwid.Padding(filler, left=1, right=1)
        return super().__init__(padding)


class RoundedLineBox(urwid.LineBox):
    """LineBox that defaults to rounded corners."""
    def __init__(self,
                 original_widget,
                 title="",
                 title_align="center",
                 title_attr=None,
                 tlcorner="\u256d",
                 tline="─",
                 lline="│",
                 trcorner="\u256e",
                 blcorner="\u2570",
                 rline="│",
                 bline="─",
                 brcorner="\u256f",
                 ) -> None:
        return super().__init__(original_widget,
                            title,
                            title_align,
                            title_attr,
                            tlcorner,
                            tline,
                            lline,
                            trcorner,
                            blcorner,
                            rline,
                            bline,
                            brcorner)
