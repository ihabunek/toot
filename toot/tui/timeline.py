import logging
import urwid

from toot.utils import format_content

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
        self._emit("status_activated", [status])

    def status_focused(self):
        """Called when the list focus switches to a new status"""
        status = self.get_focused_status()
        details = StatusDetails(status)
        self.status_details.set_body(details)

        index = self.status_list.body.focus
        count = len(self.statuses)
        self._emit("status_focused", [status, index, count])


class StatusDetails(urwid.Pile):
    def __init__(self, status):
        widget_list = list(self.content_generator(status))
        return super().__init__(widget_list)

    def content_generator(self, status):
        if status.display_name:
            yield urwid.Text(("green", status.display_name))
        yield urwid.Text(("yellow", status.account))
        yield urwid.Divider()

        for line in format_content(status.data["content"]):
            yield urwid.Text(line)

        if status.data["card"]:
            yield urwid.Divider()
            yield self.build_card(status.data["card"])

    def card_generator(self, card):
        yield urwid.Text(("green", card["title"].strip()))
        if card["author_name"]:
            yield urwid.Text(["by ", ("yellow", card["author_name"].strip())])
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
