import urwid
import logging

from .constants import VISIBILITY_OPTIONS
from .widgets import Button, EditBox
logger = logging.getLogger(__name__)


class StatusComposer(urwid.Frame):
    """
    UI for compose and posting a status message.
    """
    signals = ["close", "post"]

    def __init__(self, in_reply_to=None):
        self.in_reply_to = in_reply_to
        text, edit_pos = '', None
        if in_reply_to is not None:
            text = f'@{in_reply_to.account} '
            edit_pos = len(text)
            mentions = [f'@{m["acct"]}' for m in in_reply_to.mentions]
            if mentions:
                text += '\n\n{}'.format(' '.join(mentions))
        self.content_edit = EditBox(edit_text=text, edit_pos=edit_pos,
                                    multiline=True, allow_tab=True)

        self.cw_edit = None
        self.cw_add_button = Button("Add content warning",
            on_press=self.add_content_warning)
        self.cw_remove_button = Button("Remove content warning",
            on_press=self.remove_content_warning)

        self.visibility = "public"
        self.visibility_button = Button("Visibility: {}".format(self.visibility),
            on_press=self.choose_visibility)

        self.post_button = Button("Post", on_press=self.post)
        self.cancel_button = Button("Cancel", on_press=self.close)

        contents = list(self.generate_list_items())
        self.walker = urwid.SimpleListWalker(contents)
        self.listbox = urwid.ListBox(self.walker)
        return super().__init__(self.listbox)

    def generate_list_items(self):
        if self.in_reply_to:
            yield urwid.Text(("gray", "Replying to {}".format(self.in_reply_to.account)))
            yield urwid.AttrWrap(urwid.Divider("-"), "gray")

        yield urwid.Text("Status message")
        yield self.content_edit
        yield urwid.Divider()

        if self.cw_edit:
            yield urwid.Text("Content warning")
            yield self.cw_edit
            yield urwid.Divider()
            yield self.cw_remove_button
        else:
            yield self.cw_add_button

        yield self.visibility_button
        yield self.post_button
        yield self.cancel_button

    def refresh(self):
        self.walker = urwid.SimpleListWalker(list(self.generate_list_items()))
        self.listbox.body = self.walker

    def choose_visibility(self, *args):
        list_items = [urwid.Text("Choose status visibility:")]
        for visibility, caption, description in VISIBILITY_OPTIONS:
            text = "{} - {}".format(caption, description)
            button = Button(text, on_press=self.set_visibility, user_data=visibility)
            list_items.append(button)

        self.walker = urwid.SimpleListWalker(list_items)
        self.listbox.body = self.walker

        # Initially focus currently chosen visibility
        focus_map = {v[0]: n + 1 for n, v in enumerate(VISIBILITY_OPTIONS)}
        focus = focus_map.get(self.visibility, 1)
        self.walker.set_focus(focus)

    def set_visibility(self, widget, visibility):
        self.visibility = visibility
        self.visibility_button.set_label("Visibility: {}".format(self.visibility))
        self.refresh()
        self.walker.set_focus(7 if self.cw_edit else 4)

    def add_content_warning(self, button):
        self.cw_edit = EditBox(multiline=True, allow_tab=True)
        self.refresh()
        self.walker.set_focus(4)

    def remove_content_warning(self, button):
        self.cw_edit = None
        self.refresh()
        self.walker.set_focus(3)

    def set_error_message(self, msg):
        self.footer = urwid.Text(("footer_message_error", msg))

    def clear_error_message(self):
        self.footer = None

    def post(self, button):
        self.clear_error_message()

        # Don't lstrip content to avoid removing intentional leading whitespace
        # However, do strip both sides to check if there is any content there
        content = self.content_edit.edit_text.rstrip()
        content = None if not content.strip() else content

        warning = self.cw_edit.edit_text.rstrip() if self.cw_edit else ""
        warning = None if not warning.strip() else warning

        if not content:
            self.set_error_message("Cannot post an empty message")
            return

        in_reply_to_id = self.in_reply_to.id if self.in_reply_to else None
        self._emit("post", content, warning, self.visibility, in_reply_to_id)

    def close(self, button):
        self._emit("close")
