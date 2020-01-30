import logging
import urwid
import webbrowser

from toot.utils import format_content

from .utils import highlight_hashtags, parse_datetime, highlight_keys
from .widgets import SelectableText, SelectableColumns

logger = logging.getLogger("toot")


class Timeline(urwid.Columns):
    """
    Displays a list of statuses to the left, and status details on the right.
    """
    signals = [
        "close",      # Close thread
        "compose",    # Compose a new toot
        "delete",     # Delete own status
        "favourite",  # Favourite status
        "focus",      # Focus changed
        "media",      # Display media attachments
        "menu",       # Show a context menu
        "next",       # Fetch more statuses
        "reblog",     # Reblog status
        "reply",      # Compose a reply to a status
        "source",     # Show status source
        "links",      # Show status links
        "thread",     # Show thread for status
    ]

    def __init__(self, name, statuses, focus=0, is_thread=False):
        self.name = name
        self.is_thread = is_thread
        self.statuses = statuses
        self.status_list = self.build_status_list(statuses, focus=focus)
        self.status_details = StatusDetails(statuses[focus], is_thread)

        super().__init__([
            ("weight", 40, self.status_list),
            ("weight", 0, urwid.AttrWrap(urwid.SolidFill("│"), "blue_selected")),
            ("weight", 60, urwid.Padding(self.status_details, left=1)),
        ])

    def build_status_list(self, statuses, focus):
        items = [self.build_list_item(status) for status in statuses]
        walker = urwid.SimpleFocusListWalker(items)
        walker.set_focus(focus)
        urwid.connect_signal(walker, "modified", self.modified)
        return urwid.ListBox(walker)

    def build_list_item(self, status):
        item = StatusListItem(status)
        urwid.connect_signal(item, "click", lambda *args:
            self._emit("menu", status))
        return urwid.AttrMap(item, None, focus_map={
            "blue": "green_selected",
            "green": "green_selected",
            "yellow": "green_selected",
            "cyan": "green_selected",
            None: "green_selected",
        })

    def get_focused_status(self):
        return self.statuses[self.status_list.body.focus]

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
        self.draw_status_details(status)
        self._emit("focus")

    def refresh_status_details(self):
        """Redraws the details of the focused status."""
        status = self.get_focused_status()
        self.draw_status_details(status)

    def draw_status_details(self, status):
        self.status_details = StatusDetails(status, self.is_thread)
        self.contents[2] = urwid.Padding(self.status_details, left=1), ("weight", 60, False)

    def keypress(self, size, key):
        status = self.get_focused_status()
        command = self._command_map[key]

        # If down is pressed on last status in list emit a signal to load more.
        # TODO: Consider pre-loading statuses earlier
        if command in [urwid.CURSOR_DOWN, urwid.CURSOR_PAGE_DOWN]:
            index = self.status_list.body.focus + 1
            count = len(self.statuses)
            if index >= count:
                self._emit("next")

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

        if key in ("l", "L"):
            self._emit("links", status)
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
            self.draw_status_details(status)

    def remove_status(self, status):
        index = self.get_status_index(status.id)
        assert self.statuses[index].id == status.id  # Sanity check

        del(self.statuses[index])
        del(self.status_list.body[index])
        self.refresh_status_details()


class StatusDetails(urwid.Pile):
    def __init__(self, status, in_thread):
        """
        Parameters
        ----------
        status : Status
            The status to render.

        in_thread : bool
            Whether the status is rendered from a thread status list.
        """
        self.in_thread = in_thread
        reblogged_by = status.author if status.reblog else None
        widget_list = list(self.content_generator(status.original, reblogged_by))
        return super().__init__(widget_list)

    def content_generator(self, status, reblogged_by):
        if reblogged_by:
            text = "♺ {} boosted".format(reblogged_by.display_name or reblogged_by.username)
            yield ("pack", urwid.Text(("gray", text)))
            yield ("pack", urwid.AttrMap(urwid.Divider("-"), "gray"))

        if status.author.display_name:
            yield ("pack", urwid.Text(("green", status.author.display_name)))

        yield ("pack", urwid.Text(("yellow", status.author.account)))
        yield ("pack", urwid.Divider())

        if status.data["spoiler_text"]:
            yield ("pack", urwid.Text(status.data["spoiler_text"]))
            yield ("pack", urwid.Divider())

        # Show content warning
        if status.data["spoiler_text"] and not status.show_sensitive:
            yield ("pack", urwid.Text(("content_warning", "Marked as sensitive. Press S to view.")))
        else:
            for line in format_content(status.data["content"]):
                yield ("pack", urwid.Text(highlight_hashtags(line)))

        media = status.data["media_attachments"]
        if media:
            for m in media:
                yield ("pack", urwid.AttrMap(urwid.Divider("-"), "gray"))
                yield ("pack", urwid.Text([("bold", "Media attachment"), " (", m["type"], ")"]))
                if m["description"]:
                    yield ("pack", urwid.Text(m["description"]))
                url = m.get("text_url") or m["url"]
                yield ("pack", urwid.Text(("link", url)))

        poll = status.data.get("poll")
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
        yield ("pack", urwid.Text([
            ("gray", "⤶ {} ".format(status.data["replies_count"])),
            ("yellow" if status.reblogged else "gray", "♺ {} ".format(status.data["reblogs_count"])),
            ("yellow" if status.favourited else "gray", "★ {}".format(status.data["favourites_count"])),
            ("gray", " · {}".format(application) if application else ""),
        ]))

        # Push things to bottom
        yield ("weight", 1, urwid.SolidFill(" "))

        options = [
            "[B]oost",
            "[D]elete" if status.is_mine else "",
            "[F]avourite",
            "[V]iew",
            "[T]hread" if not self.in_thread else "",
            "[L]inks",
            "[R]eply",
            "So[u]rce",
            "[H]elp",
        ]
        options = " ".join(o for o in options if o)

        options = highlight_keys(options, "cyan_bold", "cyan")
        yield ("pack", urwid.Text(options))

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
        for option in poll["options"]:
            perc = (round(100 * option["votes_count"] / poll["votes_count"])
                if poll["votes_count"] else 0)
            yield urwid.Text(option["title"])
            yield urwid.ProgressBar("", "poll_bar", perc)

        if poll["expired"]:
            status = "Closed"
        else:
            expires_at = parse_datetime(poll["expires_at"]).strftime("%Y-%m-%d %H:%M")
            status = "Closes on {}".format(expires_at)

        status = "Poll · {} votes · {}".format(poll["votes_count"], status)
        yield urwid.Text(("gray", status))


class StatusListItem(SelectableColumns):
    def __init__(self, status):
        created_at = status.created_at.strftime("%Y-%m-%d %H:%M")
        favourited = ("yellow", "★") if status.original.favourited else " "
        reblogged = ("yellow", "♺") if status.original.reblogged else " "
        is_reblog = ("cyan", "♺") if status.reblog else " "
        is_reply = ("cyan", "⤶") if status.original.in_reply_to else " "

        return super().__init__([
            ("pack", SelectableText(("blue", created_at), wrap="clip")),
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
