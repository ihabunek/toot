import json
import traceback
import urwid
import webbrowser

from toot import __version__
from toot.utils import format_content
from .utils import highlight_hashtags, highlight_keys
from .widgets import Button, EditBox, SelectableText


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
        yes = SelectableText("Yes, send it to heck")
        no = SelectableText("No, I'll spare it for now")

        urwid.connect_signal(yes, "click", lambda *args: self._emit("delete"))
        urwid.connect_signal(no, "click", lambda *args: self._emit("close"))

        walker = urwid.SimpleFocusListWalker([
            urwid.AttrWrap(yes, "", "blue_selected"),
            urwid.AttrWrap(no, "", "blue_selected"),
        ])
        super().__init__(walker)


class GotoMenu(urwid.ListBox):
    signals = [
        "home_timeline",
        "public_timeline",
        "hashtag_timeline",
        "bookmark_timeline",
    ]

    def __init__(self, user_timelines):
        self.hash_edit = EditBox(caption="Hashtag: ")

        actions = list(self.generate_actions(user_timelines))
        walker = urwid.SimpleFocusListWalker(actions)
        super().__init__(walker)

    def get_hashtag(self):
        return self.hash_edit.edit_text.strip()

    def generate_actions(self, user_timelines):
        def _home(button):
            self._emit("home_timeline")

        def _local_public(button):
            self._emit("public_timeline", True)

        def _global_public(button):
            self._emit("public_timeline", False)

        def _bookmarks(button):
            self._emit("bookmark_timeline", False)

        def _hashtag(local):
            hashtag = self.get_hashtag()
            if hashtag:
                self._emit("hashtag_timeline", hashtag, local)
            else:
                self.set_focus(4)

        def mk_on_press_user_hashtag(tag, local):
            def on_press(btn):
                self._emit("hashtag_timeline", tag, local)
            return on_press

        yield Button("Home timeline", on_press=_home)

        for tag, cfg in user_timelines.items():
            is_local = cfg["local"]
            yield Button("#{}".format(tag) + (" (local)" if is_local else ""),
                         on_press=mk_on_press_user_hashtag(tag, is_local))

        yield Button("Local public timeline", on_press=_local_public)
        yield Button("Global public timeline", on_press=_global_public)
        yield Button("Bookmarks", on_press=_bookmarks)
        yield urwid.Divider()
        yield self.hash_edit
        yield Button("Local hashtag timeline", on_press=lambda x: _hashtag(True))
        yield Button("Public hashtag timeline", on_press=lambda x: _hashtag(False))


class Help(urwid.Padding):
    def __init__(self):
        actions = list(self.generate_contents())
        walker = urwid.SimpleListWalker(actions)
        listbox = urwid.ListBox(walker)
        super().__init__(listbox, left=1, right=1)

    def generate_contents(self):
        def h(text):
            return highlight_keys(text, "cyan")

        yield urwid.Text(("yellow_bold", "toot {}".format(__version__)))
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
        yield urwid.Text(h("  [P] - save/unsave (pin) current timeline"))
        yield urwid.Text(h("  [,] - refresh current timeline"))
        yield urwid.Text(h("  [H] - show this help"))
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
        yield urwid.Text(h("  [Z] - Open status in scrollable popup window"))
        yield urwid.Divider()
        yield urwid.Text(("bold", "Links"))
        yield urwid.Divider()
        yield link("Documentation: ", "https://toot.readthedocs.io/")
        yield link("Project home:  ", "https://github.com/ihabunek/toot/")


class Account(urwid.ListBox):
    """Shows account data and provides various actions"""
    def __init__(self, account):
        actions = list(self.generate_contents(account))
        walker = urwid.SimpleListWalker(actions)
        super().__init__(walker)

    def generate_contents(self, account):
        yield urwid.Text([('green', f"@{account['acct']}"), (f"  {account['display_name']}")])

        if account["note"]:
            yield urwid.Divider()
            for line in format_content(account["note"]):
                yield urwid.Text(highlight_hashtags(line, followed_tags=set()))

        yield urwid.Divider()
        yield urwid.Text([("ID: "), ("green", f"{account['id']}")])
        yield urwid.Text([("Since: "), ("green", f"{account['created_at'][:10]}")])
        yield urwid.Divider()

        if account["bot"]:
            yield urwid.Text([("green", "Bot \N{robot face}")])
            yield urwid.Divider()
        if account["locked"]:
            yield urwid.Text([("warning", "Locked \N{lock}")])
            yield urwid.Divider()
        if "suspended" in account and account["suspended"]:
            yield urwid.Text([("warning", "Suspended \N{cross mark}")])
            yield urwid.Divider()

        yield urwid.Text([("Followers: "), ("yellow", f"{account['followers_count']}")])
        yield urwid.Text([("Following: "), ("yellow", f"{account['following_count']}")])
        yield urwid.Text([("Statuses: "), ("yellow", f"{account['statuses_count']}")])

        if account["fields"]:
            for field in account["fields"]:
                name = field["name"].title()
                yield urwid.Divider()
                yield urwid.Text([("yellow", f"{name.rstrip(':')}"), (":")])
                for line in format_content(field["value"]):
                    yield urwid.Text(highlight_hashtags(line, followed_tags=set()))
                if field["verified_at"]:
                    yield urwid.Text(("green", "✓ Verified"))

        yield urwid.Divider()
        yield link("", account["url"])


def link(text, url):
    attr_map = {"link": "link_focused"}
    text = SelectableText([text, ("link", url)])
    urwid.connect_signal(text, "click", lambda t: webbrowser.open(url))
    return urwid.AttrMap(text, "", attr_map)
