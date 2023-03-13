import logging
import sys
import urwid
import webbrowser

from typing import Optional

from .entities import Status
from .scroll import Scrollable, ScrollBar
from .utils import highlight_hashtags, parse_datetime, highlight_keys
from .widgets import SelectableText, SelectableColumns, StatusList
from toot.utils import format_content
from toot.utils.language import language_name
from toot.tui.utils import time_ago
from urwid.util import is_mouse_press

logger = logging.getLogger("toot")


class Timeline(urwid.Columns):
    """
    Displays a list of statuses to the left, and status details on the right.
    """
    signals = [
        "account",       # Display account info and actions
        "close",         # Close thread
        "compose",       # Compose a new toot
        "delete",        # Delete own status
        "favourite",     # Favourite status
        "focus",         # Focus changed
        "bookmark",      # Bookmark status
        "media",         # Display media attachments
        "menu",          # Show a context menu
        "next",          # Fetch more statuses
        "poll",          # Vote in a poll
        "reblog",        # Reblog status
        "reply",         # Compose a reply to a status
        "source",        # Show status source
        "links",         # Show status links
        "thread",        # Show thread for status
        "translate",     # Translate status
        "save",          # Save current timeline
        "zoom",          # Open status in scrollable popup window
        "clear-screen",  # Clear the screen (used internally)
        "copy-status",   # Copy status to clipboard
    ]

    def __init__(self,
                 name,
                 statuses,
                 can_translate,
                 followed_tags=[],
                 followed_accounts=[],
                 focus=0,
                 is_thread=False):

        self.name = name
        self.is_thread = is_thread
        self.statuses = statuses
        self.can_translate = can_translate
        self.status_list = self.build_status_list(statuses, focus=focus)
        self.followed_tags = followed_tags
        self.followed_accounts = followed_accounts

        try:
            focused_status = statuses[focus]
        except IndexError:
            focused_status = None

        self.status_details = StatusDetails(self, focused_status)
        status_widget = self.wrap_status_details(self.status_details, False)
        status_list_widget = self.wrap_status_list(self.status_list, True)

        super().__init__([
            ("weight", 40, status_list_widget),
            ("weight", 0, urwid.AttrWrap(urwid.SolidFill(" "), "blue_selected")),
            ("weight", 60, status_widget),
        ])

    def wrap_status_details(self, status_details: "StatusDetails", focus=False) -> urwid.Widget:
        """Wrap StatusDetails widget with a scrollbar and footer."""
        self.status_detail_scrollable = Scrollable(urwid.Padding(status_details, right=1))
        wrapped_sd = urwid.Padding(
            urwid.Frame(
                body=ScrollBar(
                    self.status_detail_scrollable,
                    thumb_char="\u2588",
                    trough_char="\u2591",
                ),
                footer=self.get_option_text(status_details.status),
            ),
            left=1)
        if (focus):
            return urwid.LineBox(wrapped_sd)
        else:
            return urwid.LineBox(wrapped_sd,
                                 tline=" ", bline=" ", rline=" ",
                                 lline=" ", tlcorner=" ", trcorner=" ",
                                 blcorner=" ", brcorner=" ")

    def wrap_status_list(self, status_list: urwid.ListBox, focus=True) -> urwid.Widget:
        """Wrap StatusList widget with a box"""
        if (focus):
            return urwid.LineBox(status_list)
        else:
            return urwid.LineBox(status_list, tline=" ", bline=" ", rline=" ",
            lline=" ", tlcorner=" ", trcorner=" ", blcorner=" ", brcorner=" ")

    def build_status_list(self, statuses, focus):
        items = [self.build_list_item(status) for status in statuses]
        walker = urwid.SimpleFocusListWalker(items)
        walker.set_focus(focus)
        urwid.connect_signal(walker, "modified", self.modified)
        return StatusList(walker, self)

    def build_list_item(self, status):
        item = StatusListItem(status)
        urwid.connect_signal(item, "click", lambda *args:
            self._emit("menu", status))
        return urwid.AttrMap(item, None, focus_map={
            "blue": "green_selected",
            "green": "green_selected",
            "yellow": "green_selected",
            "cyan": "green_selected",
            "red": "green_selected",
            None: "green_selected",
        })

    def get_option_text(self, status: Optional[Status]) -> Optional[urwid.Text]:
        if not status:
            return None

        poll = status.original.data.get("poll")

        options = [
            "[A]ccount" if not status.is_mine else "",
            "[B]oost",
            "[D]elete" if status.is_mine else "",
            "B[o]okmark",
            "[F]avourite",
            "[V]iew",
            "[T]hread" if not self.is_thread else "",
            "[L]inks",
            "[R]eply",
            "[P]oll" if poll and not poll["expired"] else "",
            "So[u]rce",
            "[Z]oom",
            "Tra[n]slate" if self.can_translate else "",
            "Cop[y]",
            "[H]elp",
        ]
        options = "\n" + " ".join(o for o in options if o)
        options = highlight_keys(options, "white_bold", "cyan")
        return urwid.Text(options)

    def get_focused_status(self):
        try:
            return self.statuses[self.status_list.body.focus]
        except TypeError:
            return None

    def get_focused_status_with_counts(self):
        """Returns a tuple of:
            * focused status
            * focused status' index in the status list
            * length of the status list
        """
        return (
            self.get_focused_status(),
            self.status_list.body.focus,
            len(self.statuses),
        )

    def modified(self):
        """Called when the list focus switches to a new status"""
        status, index, count = self.get_focused_status_with_counts()
        self.draw_status_details(status, focus=False)
        self._emit("focus")

    def refresh_same_status_details(self, focus=None):
        """Redraws the details of the focused status."""
        pos = self.status_detail_scrollable.get_scrollpos()
        widget = self.wrap_status_details(self.status_details, focus)
        self.status_detail_scrollable.set_scrollpos(pos)
        self.contents[2] = widget, ("weight", 60, False)

    def refresh_status_details(self, focus=None):
        """Redraws the details of the focused status."""
        status = self.get_focused_status()
        pos = self.status_detail_scrollable.get_scrollpos()
        self.draw_status_details(status)
        self.status_detail_scrollable.set_scrollpos(pos)

    def draw_status_details(self, status, focus=None):
        self.status_details = StatusDetails(self, status)
        widget = self.wrap_status_details(self.status_details, focus)
        self.contents[2] = widget, ("weight", 60, False)

    def draw_status_list(self, focus=None):
        widget = self.wrap_status_list(self.status_list, focus)
        self.contents[0] = widget, ("weight", 40, False)

    def keypress(self, size, key):
        status = self.get_focused_status()
        command = self._command_map[key]

        if command in [urwid.CURSOR_RIGHT, urwid.CURSOR_MAX_RIGHT]:
            if self.focus_position == 0:
                self.draw_status_list(focus=False)
                self.refresh_same_status_details(focus=True)

        if command in [urwid.CURSOR_LEFT, urwid.CURSOR_MAX_LEFT]:
            if self.focus_position != 0:
                self.draw_status_list(focus=True)
                self.refresh_same_status_details(focus=False)

        if not status:
            return super().keypress(size, key)

        # If down is pressed on last status in list emit a signal to load more.
        # TODO: Consider pre-loading statuses earlier
        if command in [urwid.CURSOR_DOWN, urwid.CURSOR_PAGE_DOWN] \
                and self.status_list.body.focus:
            index = self.status_list.body.focus + 1
            count = len(self.statuses)
            if index >= count:
                self._emit("next")

        if key in ("a", "A"):
            self._emit("account", status.original.data['account']['id'])
            return

        if key in ("b", "B"):
            self._emit("reblog", status)
            return

        if key in ("c", "C"):
            self._emit("compose")
            return

        if key in ("d", "D"):
            self._emit("delete", status)
            return

        if key in ("f", "F"):
            self._emit("favourite", status)
            return

        if key in ("m", "M"):
            self._emit("media", status)
            return

        if key in ("q", "Q"):
            self._emit("close")
            return

        if key == "esc" and self.is_thread:
            self._emit("close")
            return

        if key in ("r", "R"):
            self._emit("reply", status)
            return

        if key in ("s", "S"):
            status.original.show_sensitive = True
            self.refresh_status_details()
            return

        if key in ("o", "O"):
            self._emit("bookmark", status)
            return

        if key in ("l", "L"):
            self._emit("links", status)
            return

        if key in ("n", "N"):
            if self.can_translate:
                self._emit("translate", status)
            return

        if key in ("t", "T"):
            self._emit("thread", status)
            return

        if key in ("u", "U"):
            self._emit("source", status)
            return

        if key in ("v", "V"):
            if status.original.url:
                webbrowser.open(status.original.url)
                # force a screen refresh; necessary with console browsers
                self._emit("clear-screen")
            return

        if key in ("e", "E"):
            self._emit("save", status)
            return

        if key in ("z", "Z"):
            self._emit("zoom", self.status_details)
            return

        if key in ("p", "P"):
            poll = status.original.data.get("poll")
            if poll and not poll["expired"]:
                self._emit("poll", status)
            return

        if key in ("y", "Y"):
            self._emit("copy-status", status)
            return

        return super().keypress(size, key)

    def append_status(self, status):
        self.statuses.append(status)
        self.status_list.body.append(self.build_list_item(status))

    def prepend_status(self, status):
        self.statuses.insert(0, status)
        self.status_list.body.insert(0, self.build_list_item(status))

    def append_statuses(self, statuses):
        for status in statuses:
            self.append_status(status)

    def get_status_index(self, id):
        # TODO: This is suboptimal, consider a better way
        for n, status in enumerate(self.statuses):
            if status.id == id:
                return n
        raise ValueError("Status with ID {} not found".format(id))

    def focus_status(self, status):
        index = self.get_status_index(status.id)
        self.status_list.body.set_focus(index)

    def update_status(self, status):
        """Overwrite status in list with the new instance and redraw."""
        index = self.get_status_index(status.id)
        assert self.statuses[index].id == status.id  # Sanity check

        # Update internal status list
        self.statuses[index] = status

        # Redraw list item
        self.status_list.body[index] = self.build_list_item(status)

        # Redraw status details if status is focused
        if index == self.status_list.body.focus:
            self.draw_status_details(status, focus=False)

    def remove_status(self, status):
        index = self.get_status_index(status.id)
        assert self.statuses[index].id == status.id  # Sanity check

        del self.statuses[index]
        del self.status_list.body[index]
        self.refresh_status_details()


class StatusDetails(urwid.Pile):
    def __init__(self, timeline: Timeline, status: Optional[Status]):
        self.status = status
        self.followed_tags = timeline.followed_tags
        self.followed_accounts = timeline.followed_accounts
        self.timeline = timeline
        reblogged_by = status.author if status and status.reblog else None
        widget_list = list(self.content_generator(status.original, reblogged_by)
            if status else ())
        return super().__init__(widget_list)

    def content_generator(self, status, reblogged_by):
        if reblogged_by:
            text = "♺ {} boosted".format(reblogged_by.display_name or reblogged_by.username)
            yield ("pack", urwid.Text(("gray", text)))
            yield ("pack", urwid.AttrMap(urwid.Divider("-"), "gray"))

        if status.author.display_name:
            yield ("pack", urwid.Text(("green", status.author.display_name)))

        account_color = "yellow" if status.author.account in self.followed_accounts else "gray"
        yield ("pack", urwid.Text((account_color, status.author.account)))
        yield ("pack", urwid.Divider())

        if status.data["spoiler_text"]:
            yield ("pack", urwid.Text(status.data["spoiler_text"]))
            yield ("pack", urwid.Divider())

        # Show content warning
        if status.data["spoiler_text"] and not status.show_sensitive:
            yield ("pack", urwid.Text(("content_warning", "Marked as sensitive. Press S to view.")))
        else:
            content = status.original.translation if status.original.show_translation else status.data["content"]
            for line in format_content(content):
                yield ("pack", urwid.Text(highlight_hashtags(line, self.followed_tags)))

            media = status.data["media_attachments"]
            if media:
                for m in media:
                    yield ("pack", urwid.AttrMap(urwid.Divider("-"), "gray"))
                    yield ("pack", urwid.Text([("bold", "Media attachment"), " (", m["type"], ")"]))
                    if m["description"]:
                        yield ("pack", urwid.Text(m["description"]))
                    yield ("pack", urwid.Text(("link", m["url"])))

            poll = status.original.data.get("poll")
            if poll:
                yield ("pack", urwid.Divider())
                yield ("pack", self.build_linebox(self.poll_generator(poll)))

            card = status.data.get("card")
            if card:
                yield ("pack", urwid.Divider())
                yield ("pack", self.build_linebox(self.card_generator(card)))

        application = status.data.get("application") or {}
        application = application.get("name")

        yield ("pack", urwid.AttrWrap(urwid.Divider("-"), "gray"))

        translated_from = (
            language_name(status.original.translated_from)
            if status.original.show_translation and status.original.translated_from
            else None
        )

        visibility_colors = {
            "public": "gray",
            "unlisted": "white",
            "private": "cyan",
            "direct": "yellow"
        }

        visibility = status.visibility.title()
        visibility_color = visibility_colors.get(status.visibility, "gray")

        yield ("pack", urwid.Text([
            ("blue", f"{status.created_at.strftime('%Y-%m-%d %H:%M')} "),
            ("red" if status.bookmarked else "gray", "b "),
            ("gray", f"⤶ {status.data['replies_count']} "),
            ("yellow" if status.reblogged else "gray", f"♺ {status.data['reblogs_count']} "),
            ("yellow" if status.favourited else "gray", f"★ {status.data['favourites_count']}"),
            (visibility_color, f" · {visibility}"),
            ("yellow", f" · Translated from {translated_from} " if translated_from else ""),
            ("gray", f" · {application}" if application else ""),
        ]))

        # Push things to bottom
        yield ("weight", 1, urwid.BoxAdapter(urwid.SolidFill(" "), 1))

    def build_linebox(self, contents):
        contents = urwid.Pile(list(contents))
        contents = urwid.Padding(contents, left=1, right=1)
        return urwid.LineBox(contents)

    def card_generator(self, card):
        yield urwid.Text(("green", card["title"].strip()))
        if card.get("author_name"):
            yield urwid.Text(["by ", ("yellow", card["author_name"].strip())])
        yield urwid.Text("")
        if card["description"]:
            yield urwid.Text(card["description"].strip())
            yield urwid.Text("")
        yield urwid.Text(("link", card["url"]))

    def poll_generator(self, poll):
        for idx, option in enumerate(poll["options"]):
            perc = (round(100 * option["votes_count"] / poll["votes_count"])
                if poll["votes_count"] else 0)

            if poll["voted"] and poll["own_votes"] and idx in poll["own_votes"]:
                voted_for = " ✓"
            else:
                voted_for = ""

            yield urwid.Text(option["title"] + voted_for)
            yield urwid.ProgressBar("", "poll_bar", perc)

        status = "Poll · {} votes".format(poll["votes_count"])

        if poll["expired"]:
            status += " · Closed"

        if poll["expires_at"]:
            expires_at = parse_datetime(poll["expires_at"]).strftime("%Y-%m-%d %H:%M")
            status += " · Closes on {}".format(expires_at)

        yield urwid.Text(("gray", status))

    def mouse_event(self, size, event, button, col, row, focus):
        if is_mouse_press(event) and button == 1:
            self.timeline.draw_status_list(focus=False)
            self.timeline.refresh_same_status_details(focus=True)
        return super().mouse_event(size, event, button, col, row, focus)


class StatusListItem(SelectableColumns):
    def __init__(self, status):
        edited_at = status.data.get("edited_at")

        # TODO: hacky implementation to avoid creating conflicts for existing
        # pull reuqests, refactor when merged.
        created_at = (
            time_ago(status.created_at).ljust(3, " ")
            if "--relative-datetimes" in sys.argv
            else status.created_at.strftime("%Y-%m-%d %H:%M")
        )

        edited_flag = "*" if edited_at else " "
        favourited = ("yellow", "★") if status.original.favourited else " "
        reblogged = ("yellow", "♺") if status.original.reblogged else " "
        is_reblog = ("cyan", "♺") if status.reblog else " "
        is_reply = ("cyan", "⤶") if status.original.in_reply_to else " "

        return super().__init__([
            ("pack", SelectableText(("blue", created_at), wrap="clip")),
            ("pack", urwid.Text(("blue", edited_flag))),
            ("pack", urwid.Text(" ")),
            ("pack", urwid.Text(favourited)),
            ("pack", urwid.Text(" ")),
            ("pack", urwid.Text(reblogged)),
            ("pack", urwid.Text(" ")),
            urwid.Text(("green", status.original.account), wrap="clip"),
            ("pack", urwid.Text(is_reply)),
            ("pack", urwid.Text(is_reblog)),
            ("pack", urwid.Text(" ")),
        ])
