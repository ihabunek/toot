import logging
import urwid

from .widgets import SelectableText, SelectableColumns

logger = logging.getLogger("toot")


class Timeline(urwid.Columns):
    """
    Displays a list of statuses to the left, and status details on the right.

    TODO: Switch to top/bottom for narrow views.
    """

    signals = ["status_focused"]

    def __init__(self, tui, statuses):
        self.tui = tui
        self.statuses = statuses
        self.instance = tui.app.instance

        self.status_list = self.build_status_list(statuses)
        self.status_details = self.build_status_details(statuses[0], self.instance)

        # TODO:
        # self.status_cache = {}

        super().__init__([
            ("weight", 50, self.status_list),
            ("weight", 50, self.status_details),
        ], dividechars=1)

    def build_status_list(self, statuses):
        items = [self.list_item(status) for status in statuses]
        walker = urwid.SimpleFocusListWalker(items)
        urwid.connect_signal(walker, "modified", self.status_focused)
        return urwid.ListBox(walker)

    def build_status_details(self, status, instance):
        details = StatusDetails(status, instance)
        return urwid.Filler(details, valign="top")

    def get_focused_status(self):
        return self.statuses[self.status_list.body.focus]

    def status_activated(self, *args):
        """Called when a status is clicked, or Enter is pressed."""
        # logger.info("status_activated " + str(args))

    def status_focused(self):
        """Called when the list focus switches to a new status"""
        status = self.get_focused_status()
        details = StatusDetails(status, self.instance)
        self.status_details.set_body(details)
        self._emit("status_focused", [status])

    def list_item(self, status):
        item = StatusListItem(status, self.instance)
        urwid.connect_signal(item, "click", self.status_activated)
        return urwid.AttrMap(item, None, focus_map={
            "blue": "green_selected",
            "green": "green_selected",
            "yellow": "green_selected",
            None: "green_selected",
        })


class StatusDetails(urwid.Pile):
    def __init__(self, status, instance):
        return super().__init__([
            urwid.Text(status.id)
        ])



class StatusListItem(SelectableColumns):
    def __init__(self, status, instance):
        created_at = status.created_at.strftime("%Y-%m-%d %H:%M")
        favourited = ("yellow", "★") if status.data["favourited"] else " "
        reblogged = ("yellow", "⤶") if status.data["reblogged"] else " "

        return super().__init__([
            ("pack", SelectableText(("blue", created_at), wrap="clip")),
            ("pack", urwid.Text(" ")),
            urwid.Text(("green", status.account), wrap="clip"),
            ("pack", urwid.Text(" ")),
            ("pack", urwid.Text(favourited)),
            ("pack", urwid.Text(reblogged)),
        ])
