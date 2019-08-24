import logging
import urwid
import webbrowser

from toot.utils import format_content

from .utils import highlight_hashtags
from .widgets import SelectableText, SelectableColumns

logger = logging.getLogger("toot")


class Timeline(urwid.Columns):
    """
    Displays a list of statuses to the left, and status details on the right.

    TODO: Switch to top/bottom for narrow views.
    TODO: Cache rendered statuses?
    """
    signals = [
        "status_focused",
        "status_activated",
        "next",
    ]

    def __init__(self, tui, statuses):
        self.tui = tui
        self.statuses = statuses
        self.instance = tui.app.instance

        self.status_list = self.build_status_list(statuses)
        self.status_details = self.build_status_details(statuses[0])

        super().__init__([
            ("weight", 50, self.status_list),
            ("weight", 50, self.status_details),
        ], dividechars=1)

    def build_status_list(self, statuses):
        items = [self.build_list_item(status) for status in statuses]
        walker = urwid.SimpleFocusListWalker(items)
        urwid.connect_signal(walker, "modified", self.status_focused)
        return urwid.ListBox(walker)

    def build_list_item(self, status):
        item = StatusListItem(status)
        urwid.connect_signal(item, "click", self.status_activated)
        return urwid.AttrMap(item, None, focus_map={
            "blue": "green_selected",
            "green": "green_selected",
            "yellow": "green_selected",
            None: "green_selected",
        })

    def build_status_details(self, status):
        details = StatusDetails(status)
        return urwid.Filler(details, valign="top")

    def get_focused_status(self):
        return self.statuses[self.status_list.body.focus]

    def status_activated(self, *args):
        """Called when a status is clicked, or Enter is pressed."""
        status = self.get_focused_status()
        self._emit("status_activated", [status])

    def status_focused(self):
        """Called when the list focus switches to a new status"""
        status = self.get_focused_status()
        details = StatusDetails(status)
        self.status_details.set_body(details)

        index = self.status_list.body.focus
        count = len(self.statuses)
        self._emit("status_focused", [status, index, count])

    def keypress(self, size, key):
        # If down is pressed on last status in list emit a signal to load more.
        # TODO: Consider pre-loading statuses earlier
        command = self._command_map[key]
        if command in [urwid.CURSOR_DOWN, urwid.CURSOR_PAGE_DOWN]:
            index = self.status_list.body.focus + 1
            count = len(self.statuses)
            if index >= count:
                self._emit("next")

        if key in ("v", "V"):
            status = self.get_focused_status()
            webbrowser.open(status.data["url"])
            return

        return super().keypress(size, key)

    def add_statuses(self, statuses):
        self.statuses += statuses
        new_items = [self.build_list_item(status) for status in statuses]
        self.status_list.body.extend(new_items)


class StatusDetails(urwid.Pile):
    def __init__(self, status):
        widget_list = list(self.content_generator(status))
        return super().__init__(widget_list)

    def content_generator(self, status):
        if status.data["reblog"]:
            yield urwid.Text([
                ("gray", "Reblogged by "),
                ("gray", status.data["account"]["display_name"])
            ])
            yield urwid.AttrMap(urwid.Divider("-"), "gray")

        if status.author.display_name:
            yield urwid.Text(("green", status.author.display_name))
        yield urwid.Text(("yellow", status.author.account))
        yield urwid.Divider()

        for line in format_content(status.data["content"]):
            yield urwid.Text(highlight_hashtags(line))

        if status.data["card"]:
            yield urwid.Divider()
            yield self.build_card(status.data["card"])

    def card_generator(self, card):
        yield urwid.Text(("green", card["title"].strip()))
        if card["author_name"]:
            yield urwid.Text(["by ", ("yellow", card["author_name"].strip())])
        yield urwid.Text("")
        if card["description"]:
            yield urwid.Text(card["description"].strip())
            yield urwid.Text("")
        yield urwid.Text(("link", card["url"]))

    def build_card(self, card):
        contents = list(self.card_generator(card))
        return urwid.LineBox(urwid.Pile(contents))


class StatusListItem(SelectableColumns):
    def __init__(self, status):
        created_at = status.created_at.strftime("%Y-%m-%d %H:%M")
        favourited = ("yellow", "★") if status.favourited else " "
        reblogged = ("yellow", "⤶") if status.reblogged else " "

        return super().__init__([
            ("pack", SelectableText(("blue", created_at), wrap="clip")),
            ("pack", urwid.Text(" ")),
            urwid.Text(("green", status.account), wrap="clip"),
            ("pack", urwid.Text(" ")),
            ("pack", urwid.Text(favourited)),
            ("pack", urwid.Text(" ")),
            ("pack", urwid.Text(reblogged)),
        ])
