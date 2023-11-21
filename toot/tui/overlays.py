import json
import traceback
import urwid
import webbrowser

from toot import __version__
from toot import api
from toot.tui.utils import highlight_keys
from toot.tui.widgets import Button, EditBox, SelectableText
from toot.tui.richtext import html_to_widgets


class StatusSource(urwid.Padding):
    """Shows status data, as returned by the server, as formatted JSON."""
    def __init__(self, status):
        self.source = json.dumps(status.data, indent=4)
        self.filename_edit = EditBox(caption="Filename: ", edit_text=f"status-{status.id}.json")
        self.status_text = urwid.Text("")

        walker = urwid.SimpleFocusListWalker([
            self.filename_edit,
            Button("Save", on_press=self.save_json),
            urwid.Divider("─"),
            urwid.Divider(" "),
            urwid.Text(self.source)
        ])

        frame = urwid.Frame(
            body=urwid.ListBox(walker),
            footer=self.status_text
        )
        super().__init__(frame)

    def save_json(self, button):
        filename = self.filename_edit.get_edit_text()
        if filename:
            with open(filename, "w") as f:
                f.write(self.source)
            self.status_text.set_text(("footer_message", f"Saved to {filename}"))


class StatusZoom(urwid.ListBox):
    """Opens status in scrollable popup window"""
    def __init__(self, status_details):
        ll = list(filter(lambda x: getattr(x, "rows", None), status_details.widget_list))
        walker = urwid.SimpleFocusListWalker(ll)
        super().__init__(walker)


class StatusLinks(urwid.ListBox):
    """Shows status links."""
    signals = ["clear-screen"]

    def __init__(self, links):

        def widget(url, title):
            return Button(title or url, on_press=lambda btn: self.browse(url))

        walker = urwid.SimpleFocusListWalker(
            [widget(url, title) for url, title in links]
        )
        super().__init__(walker)

    def browse(self, url):
        webbrowser.open(url)
        # force a screen refresh; necessary with console browsers
        self._emit("clear-screen")


class ExceptionStackTrace(urwid.ListBox):
    """Shows an exception stack trace."""
    def __init__(self, ex):
        lines = traceback.format_exception(type(ex), value=ex, tb=ex.__traceback__)
        walker = urwid.SimpleFocusListWalker([
            urwid.Text(line) for line in lines
        ])
        super().__init__(walker)


class StatusDeleteConfirmation(urwid.ListBox):
    signals = ["delete", "close"]

    def __init__(self, status):
        def _delete(_):
            self._emit("delete")

        def _close(_):
            self._emit("close")

        walker = urwid.SimpleFocusListWalker([
            Button("Yes, delete", on_press=_delete),
            Button("No, cancel", on_press=_close),
        ])
        super().__init__(walker)


class GotoMenu(urwid.ListBox):
    signals = [
        "home_timeline",
        "public_timeline",
        "hashtag_timeline",
        "bookmark_timeline",
        "notification_timeline",
        "conversation_timeline",
        "personal_timeline",
        "list_timeline",
    ]

    def __init__(self, user_timelines, user_lists):
        self.hash_edit = EditBox(caption="Hashtag: ")
        self.message_widget = urwid.Text("")

        actions = list(self.generate_actions(user_timelines, user_lists))
        walker = urwid.SimpleFocusListWalker(actions)
        super().__init__(walker)

    def get_hashtag(self):
        return self.hash_edit.edit_text.strip().lstrip("#")

    def generate_actions(self, user_timelines, user_lists):
        def _home(button):
            self._emit("home_timeline")

        def _local_public(button):
            self._emit("public_timeline", True)

        def _global_public(button):
            self._emit("public_timeline", False)

        def _personal(button):
            self._emit("personal_timeline", False)

        def _bookmarks(button):
            self._emit("bookmark_timeline", False)

        def _notifications(button):
            self._emit("notification_timeline", False)

        def _conversations(button):
            self._emit("conversation_timeline", False)

        def _hashtag(local):
            self.message_widget.set_text("")
            hashtag = self.get_hashtag()
            if hashtag:
                self._emit("hashtag_timeline", hashtag, local)
            else:
                self.message_widget.set_text(("warning", "Hashtag name required"))

        def mk_on_press_user_hashtag(tag, local):
            def on_press(btn):
                self._emit("hashtag_timeline", tag, local)
            return on_press

        def mk_on_press_user_list(list_item):
            def on_press(btn):
                self._emit("list_timeline", list_item)
            return on_press

        yield Button("Home timeline", on_press=_home)
        yield Button("Local public timeline", on_press=_local_public)
        yield Button("Global public timeline", on_press=_global_public)
        yield Button("Personal timeline", on_press=_personal)
        yield Button("Bookmarks", on_press=_bookmarks)
        yield Button("Notifications", on_press=_notifications)
        yield Button("Conversations", on_press=_conversations)

        if len(user_timelines):
            yield urwid.Divider()
            yield urwid.Text(("bold", "Shortcuts:"))

            # show all hashtag shortcuts
            for tag, cfg in sorted(user_timelines.items()):
                is_local = cfg["local"]
                yield Button(f"#{tag}" + (" (local)" if is_local else ""),
                     on_press=mk_on_press_user_hashtag(tag, is_local))

        for list_item in user_lists:
            yield Button(f"\N{clipboard}{list_item['title']}",
                         on_press=mk_on_press_user_list(list_item))

        yield urwid.Divider()
        yield self.hash_edit
        yield Button("Local hashtag timeline", on_press=lambda x: _hashtag(True))
        yield Button("Public hashtag timeline", on_press=lambda x: _hashtag(False))
        yield urwid.Divider()
        yield self.message_widget


class Help(urwid.Padding):
    def __init__(self):
        actions = list(self.generate_contents())
        walker = urwid.SimpleListWalker(actions)
        listbox = urwid.ListBox(walker)
        super().__init__(listbox, left=1, right=1)

    def generate_contents(self):
        def h(text):
            return highlight_keys(text, "shortcut")

        yield urwid.Text(("bold", "toot {}".format(__version__)))
        yield urwid.Divider()
        yield urwid.Text(("bold", "General usage"))
        yield urwid.Divider()
        yield urwid.Text(h("  [Arrow keys] or [H/J/K/L] to move around and scroll content"))
        yield urwid.Text(h("  [PageUp] and [PageDown] to scroll content"))
        yield urwid.Text(h("  [Enter] or [Space] to activate buttons and menu options"))
        yield urwid.Text(h("  [Esc] or [Q] to go back, close overlays, such as menus and this help text"))
        yield urwid.Divider()
        yield urwid.Text(("bold", "General keys"))
        yield urwid.Divider()
        yield urwid.Text(h("  [Q] - quit toot"))
        yield urwid.Text(h("  [G] - go to - switch timelines"))
        yield urwid.Text(h("  [E] - save/unsave (pin) current timeline"))
        yield urwid.Text(h("  [,] - refresh current timeline"))
        yield urwid.Text(h("  [?] - show this help"))
        yield urwid.Divider()
        yield urwid.Text(("bold", "Status keys"))
        yield urwid.Divider()
        yield urwid.Text("These commands are applied to the currently focused status.")
        yield urwid.Divider()
        yield urwid.Text(h("  [B] - Boost/unboost status"))
        yield urwid.Text(h("  [C] - Compose new status"))
        yield urwid.Text(h("  [F] - Favourite/unfavourite status"))
        yield urwid.Text(h("  [K] - Bookmark/unbookmark status"))
        yield urwid.Text(h("  [N] - Translate status if possible (toggle)"))
        yield urwid.Text(h("  [R] - Reply to current status"))
        yield urwid.Text(h("  [S] - Show text marked as sensitive"))
        yield urwid.Text(h("  [T] - Show status thread (replies)"))
        yield urwid.Text(h("  [L] - Show the status links"))
        yield urwid.Text(h("  [U] - Show the status data in JSON as received from the server"))
        yield urwid.Text(h("  [V] - Open status in default browser"))
        yield urwid.Text(h("  [Y] - Copy status to clipboard"))
        yield urwid.Text(h("  [Z] - Open status in scrollable popup window"))
        yield urwid.Divider()
        yield urwid.Text(("bold", "Links"))
        yield urwid.Divider()
        yield link("Documentation: ", "https://toot.bezdomni.net/")
        yield link("Project home:  ", "https://github.com/ihabunek/toot/")


class Account(urwid.ListBox):
    """Shows account data and provides various actions"""
    def __init__(self, app, user, account, relationship):
        self.app = app
        self.user = user
        self.account = account
        self.relationship = relationship
        self.last_action = None
        self.setup_listbox()

    def setup_listbox(self):
        actions = list(self.generate_contents(self.account, self.relationship, self.last_action))
        walker = urwid.SimpleListWalker(actions)
        super().__init__(walker)

    def generate_contents(self, account, relationship=None, last_action=None):
        if self.last_action and not self.last_action.startswith("Confirm"):
            yield Button(f"Confirm {self.last_action}", on_press=take_action, user_data=self)
            yield Button("Cancel", on_press=cancel_action, user_data=self)
        else:
            if self.user.username == account["acct"]:
                yield urwid.Text(("dim", "This is your account"))
            else:
                if relationship['requested']:
                    yield urwid.Text(("dim", "< Follow request is pending >"))
                else:
                    yield Button("Unfollow" if relationship['following'] else "Follow",
                    on_press=confirm_action, user_data=self)

                yield Button("Unmute" if relationship['muting'] else "Mute",
                    on_press=confirm_action, user_data=self)
                yield Button("Unblock" if relationship['blocking'] else "Block",
                    on_press=confirm_action, user_data=self)

        yield urwid.Divider("─")
        yield urwid.Divider()
        yield urwid.Text([("account", f"@{account['acct']}"), f"  {account['display_name']}"])

        if account["note"]:
            yield urwid.Divider()

            widgetlist = html_to_widgets(account["note"])
            for line in widgetlist:
                yield (line)

        yield urwid.Divider()
        yield urwid.Text(["ID: ", ("highlight", f"{account['id']}")])
        yield urwid.Text(["Since: ", ("highlight", f"{account['created_at'][:10]}")])
        yield urwid.Divider()

        if account["bot"]:
            yield urwid.Text([("highlight", "Bot \N{robot face}")])
            yield urwid.Divider()
        if account["locked"]:
            yield urwid.Text([("warning", "Locked \N{lock}")])
            yield urwid.Divider()
        if "suspended" in account and account["suspended"]:
            yield urwid.Text([("warning", "Suspended \N{cross mark}")])
            yield urwid.Divider()
        if relationship["followed_by"]:
            yield urwid.Text(("highlight", "Follows you \N{busts in silhouette}"))
            yield urwid.Divider()
        if relationship["blocked_by"]:
            yield urwid.Text(("warning", "Blocks you \N{no entry}"))
            yield urwid.Divider()

        yield urwid.Text(["Followers: ", ("highlight", f"{account['followers_count']}")])
        yield urwid.Text(["Following: ", ("highlight", f"{account['following_count']}")])
        yield urwid.Text(["Statuses: ", ("highlight", f"{account['statuses_count']}")])

        if account["fields"]:
            for field in account["fields"]:
                name = field["name"].title()
                yield urwid.Divider()
                yield urwid.Text([("bold", f"{name.rstrip(':')}"), ":"])

                widgetlist = html_to_widgets(field["value"])
                for line in widgetlist:
                    yield (line)

                if field["verified_at"]:
                    yield urwid.Text(("success", "✓ Verified"))

        yield urwid.Divider()
        yield link("", account["url"])


def take_action(button: Button, self: Account):
    action = button.get_label()

    if action == "Confirm Follow":
        self.relationship = api.follow(self.app, self.user, self.account["id"]).json()
    elif action == "Confirm Unfollow":
        self.relationship = api.unfollow(self.app, self.user, self.account["id"]).json()
    elif action == "Confirm Mute":
        self.relationship = api.mute(self.app, self.user, self.account["id"]).json()
    elif action == "Confirm Unmute":
        self.relationship = api.unmute(self.app, self.user, self.account["id"]).json()
    elif action == "Confirm Block":
        self.relationship = api.block(self.app, self.user, self.account["id"]).json()
    elif action == "Confirm Unblock":
        self.relationship = api.unblock(self.app, self.user, self.account["id"]).json()

    self.last_action = None
    self.setup_listbox()


def confirm_action(button: Button, self: Account):
    self.last_action = button.get_label()
    self.setup_listbox()


def cancel_action(button: Button, self: Account):
    self.last_action = None
    self.setup_listbox()


def link(text, url):
    attr_map = {"link": "link_focused"}
    text = SelectableText([text, ("link", url)])
    urwid.connect_signal(text, "click", lambda t: webbrowser.open(url))
    return urwid.AttrMap(text, "", attr_map)
