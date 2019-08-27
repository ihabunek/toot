import urwid
import logging

logger = logging.getLogger(__name__)


class EditBox(urwid.AttrWrap):
    def __init__(self):
        edit = urwid.Edit(multiline=True, allow_tab=True)
        return super().__init__(edit, "editbox", "editbox_focused")


class Button(urwid.AttrWrap):
    def __init__(self, *args, **kwargs):
        button = urwid.Button(*args, **kwargs)
        padding = urwid.Padding(button, width=len(args[0]) + 4)
        return super().__init__(padding, "button", "button_focused")

    def set_label(self, *args, **kwargs):
        self.original_widget.original_widget.set_label(*args, **kwargs)
        self.original_widget.width = len(args[0]) + 4


class StatusComposer(urwid.Frame):
    signals = ["close", "post"]

    def __init__(self):
        # This can be added by button press
        self.content = EditBox()
        self.content_warning = None
        self.cw_button = Button("Add content warning", on_press=self.toggle_cw)

        contents = [
            urwid.Text("Status message"),
            self.content,
            urwid.Divider(),
            self.cw_button,
            Button("Post", on_press=self.post),
            Button("Cancel", on_press=self.close),
        ]

        self.walker = urwid.SimpleListWalker(contents)
        self.listbox = urwid.ListBox(self.walker)
        return super().__init__(self.listbox)

    def toggle_cw(self, button):
        if self.content_warning:
            self.cw_button.set_label("Add content warning")
            self.walker.pop(2)
            self.walker.pop(2)
            self.walker.pop(2)
            self.walker.set_focus(3)
            self.content_warning = None
        else:
            self.cw_button.set_label("Remove content warning")
            self.content_warning = EditBox()
            self.walker.insert(2, self.content_warning)
            self.walker.insert(2, urwid.Text("Content warning"))
            self.walker.insert(2, urwid.Divider())
            self.walker.set_focus(4)

    def clear_error_message(self):
        self.footer = None

    def set_error_message(self, msg):
        self.footer = urwid.Text(("footer_message_error", msg))

    def post(self, button):
        self.clear_error_message()

        # Don't lstrip content to avoid removing intentional leading whitespace
        # However, do strip both sides to check if there is any content there
        content = self.content.edit_text.rstrip()
        content = None if not content.strip() else content

        warning = (self.content_warning.edit_text.rstrip()
            if self.content_warning else "")
        warning = None if not warning.strip() else warning

        if not content:
            self.set_error_message("Cannot post an empty message")
            return

        self._emit("post", content, warning)

    def close(self, button):
        self._emit("close")
