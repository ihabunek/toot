import logging
import math
import urwid
import webbrowser

from typing import List, Optional

from toot.tui import app

from toot.tui.richtext import html_to_widgets, url_to_widget
from toot.utils.datetime import parse_datetime, time_ago
from toot.utils.language import language_name

from toot.entities import Status
from toot.tui.scroll import Scrollable, ScrollBar

from toot.tui.utils import highlight_keys
from toot.tui.images import image_support_enabled, graphics_widget, can_render_pixels
from toot.tui.widgets import SelectableText, SelectableColumns, RoundedLineBox


logger = logging.getLogger("toot")
screen = urwid.raw_display.Screen()


class Timeline(urwid.Columns):
    """
    Displays a list of statuses to the left, and status details on the right.
    """

    signals = [
        "close",  # Close thread
        "focus",  # Focus changed
        "next",   # Fetch more statuses
        "save",   # Save current timeline
    ]

    def __init__(
        self,
        tui: "app.TUI",
        name: str,
        statuses: List[Status],
        focus: int = 0,
        is_thread: bool = False
    ):
        self.tui = tui
        self.name = name
        self.is_thread = is_thread
        self.statuses = statuses
        self.status_list = self.build_status_list(statuses, focus=focus)
        self.can_render_pixels = can_render_pixels(self.tui.options.image_format)

        try:
            focused_status = statuses[focus]
        except IndexError:
            focused_status = None

        self.status_details = StatusDetails(self, focused_status)
        status_widget = self.wrap_status_details(self.status_details)

        super().__init__([
            ("weight", 40, self.status_list),
            ("weight", 0, urwid.AttrWrap(urwid.SolidFill("│"), "columns_divider")),
            ("weight", 60, status_widget),
        ])

    def wrap_status_details(self, status_details: "StatusDetails") -> urwid.Widget:
        """Wrap StatusDetails widget with a scrollbar and footer."""
        self.status_detail_scrollable = Scrollable(urwid.Padding(status_details, right=1))
        return urwid.Padding(
            urwid.Frame(
                body=ScrollBar(
                    self.status_detail_scrollable,
                    thumb_char="\u2588",
                    trough_char="\u2591",
                ),
                footer=self.get_option_text(status_details.status),
            ),
            left=1
        )

    def build_status_list(self, statuses, focus):
        items = [self.build_list_item(status) for status in statuses]
        walker = urwid.SimpleFocusListWalker(items)
        walker.set_focus(focus)
        urwid.connect_signal(walker, "modified", self.modified)
        return urwid.ListBox(walker)

    def build_list_item(self, status):
        item = StatusListItem(status, self.tui.options.relative_datetimes)
        urwid.connect_signal(item, "click", lambda *args:
            self.tui.show_context_menu(status))
        return urwid.AttrMap(item, None, focus_map={
            "status_list_account": "status_list_selected",
            "status_list_timestamp": "status_list_selected",
            "highlight": "status_list_selected",
            "dim": "status_list_selected",
            None: "status_list_selected",
        })

    def get_option_text(self, status: Optional[Status]) -> Optional[urwid.Text]:
        if not status:
            return None

        poll = status.original.data.get("poll")
        show_media = status.original.data["media_attachments"] and self.tui.options.media_viewer

        options = [
            "[A]ccount" if not status.is_mine else "",
            "[B]oost",
            "[D]elete" if status.is_mine else "",
            "[E]dit" if status.is_mine else "",
            "B[o]okmark",
            "[F]avourite",
            "[V]iew",
            "[T]hread" if not self.is_thread else "",
            "L[i]nks",
            "[M]edia" if show_media else "",
            "[R]eply",
            "[P]oll" if poll and not poll["expired"] else "",
            "So[u]rce",
            "[Z]oom",
            "Tra[n]slate" if self.tui.can_translate else "",
            "Cop[y]",
            "Help([?])",
        ]
        options = "\n" + " ".join(o for o in options if o)
        options = highlight_keys(options, "shortcut_highlight", "shortcut")
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

        if image_support_enabled:
            clear_op = getattr(self.tui.screen, "clear_images", None)
            # term-image's screen implementation has clear_images(),
            # urwid's implementation does not.
            # TODO: it would be nice not to check this each time thru

            if callable(clear_op):
                self.tui.screen.clear_images()

        self.draw_status_details(status)
        self._emit("focus")

    def refresh_status_details(self):
        """Redraws the details of the focused status."""
        status = self.get_focused_status()
        pos = self.status_detail_scrollable.get_scrollpos()
        self.draw_status_details(status)
        self.status_detail_scrollable.set_scrollpos(pos)

    def draw_status_details(self, status):
        self.status_details = StatusDetails(self, status)
        widget = self.wrap_status_details(self.status_details)
        self.contents[2] = widget, ("weight", 60, False)

    def keypress(self, size, key):
        status = self.get_focused_status()
        command = self._command_map[key]

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
            account_id = status.original.data["account"]["id"]
            self.tui.show_account(account_id)
            return

        if key in ("b", "B"):
            self.tui.async_toggle_reblog(self, status)
            return

        if key in ("c", "C"):
            self.tui.show_compose()
            return

        if key in ("d", "D"):
            if status.is_mine:
                self.tui.show_delete_confirmation(status)
            return

        if key in ("e", "E"):
            if status.is_mine:
                self.tui.async_edit(status)
            return

        if key in ("f", "F"):
            self.tui.async_toggle_favourite(self, status)
            return

        if key in ("m", "M"):
            self.tui.show_media(status)
            return

        if key in ("q", "Q"):
            self._emit("close")
            return

        if key == "esc" and self.is_thread:
            self._emit("close")
            return

        if key in ("r", "R"):
            self.tui.show_compose(status)
            return

        if key in ("s", "S"):
            status.original.show_sensitive = True
            self.refresh_status_details()
            return

        if key in ("o", "O"):
            self.tui.async_toggle_bookmark(self, status)
            return

        if key in ("i", "I"):
            self.tui.show_links(status)
            return

        if key in ("n", "N"):
            if self.tui.can_translate:
                self.tui.async_translate(self, status)
            return

        if key in ("t", "T"):
            self.tui.show_thread(status)
            return

        if key in ("u", "U"):
            self.tui.show_status_source(status)
            return

        if key in ("v", "V"):
            if status.original.url:
                webbrowser.open(status.original.url)
                # force a screen refresh; necessary with console browsers
                self.tui.clear_screen()
            return

        if key in ("e", "E"):
            self._emit("save", status)
            return

        if key in ("z", "Z"):
            self.tui.show_status_zoom(self.status_details)
            return

        if key in ("p", "P"):
            poll = status.original.data.get("poll")
            if poll and not poll["expired"]:
                self.tui.show_poll(status)
            return

        if key in ("y", "Y"):
            self.tui.copy_status(status)
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
        for n, status in enumerate(self.statuses.copy()):
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

    def update_status_image(self, status, path, placeholder_index):
        """Replace image placeholder with image widget and redraw"""
        index = self.get_status_index(status.id)
        assert self.statuses[index].id == status.id  # Sanity check

        # get the image and replace the placeholder with a graphics widget
        img = None
        if hasattr(self, "images"):
            try:
                img = self.images[(str(hash(path)))]
            except KeyError:
                pass
        if img:
            try:
                status.placeholders[placeholder_index]._set_original_widget(
                    graphics_widget(img, image_format=self.tui.options.image_format, corner_radius=10,
                                    colors=self.tui.options.colors))

            except IndexError:
                # ignore IndexErrors.
                pass

    def remove_status(self, status):
        index = self.get_status_index(status.id)
        assert self.statuses[index].id == status.id  # Sanity check

        del self.statuses[index]
        del self.status_list.body[index]
        self.refresh_status_details()


class StatusDetails(urwid.Pile):
    def __init__(self, timeline: Timeline, status: Optional[Status]):
        self.status = status
        self.timeline = timeline
        if self.status:
            self.status.placeholders = []
        self.followed_accounts = timeline.tui.followed_accounts
        self.options = timeline.tui.options

        reblogged_by = status.author if status and status.reblog else None
        widget_list = list(self.content_generator(status.original, reblogged_by)
            if status else ())
        return super().__init__(widget_list)

    def image_widget(self, path, rows=None, aspect=None) -> urwid.Widget:
        """Returns a widget capable of displaying the image

        path is required; URL to image
        rows, if specfied, sets a fixed number of rows. Or:
        aspect, if specified, calculates rows based on pane width
        and the aspect ratio provided"""

        if not rows:
            if not aspect:
                aspect = 3 / 2  # reasonable default

            screen_rows = screen.get_cols_rows()[1]
            if self.timeline.can_render_pixels:
                # for pixel-rendered images,
                # image rows should be 33% of the available screen
                # but in no case fewer than 10
                rows = max(10, math.floor(screen_rows * .33))
            else:
                # for cell-rendered images,
                # use the max available columns
                # and calculate rows based on the image
                # aspect ratio
                cols = math.floor(0.55 * screen.get_cols_rows()[0])
                rows = math.ceil((cols / 2) / aspect)
                # if the calculated rows are more than will
                # fit on one screen, reduce to one screen of rows
                rows = min(screen_rows - 6, rows)

                # but in no case fewer than 10 rows
                rows = max(rows, 10)

        img = None
        if hasattr(self.timeline, "images"):
            try:
                img = self.timeline.images[(str(hash(path)))]
            except KeyError:
                pass
        if img:
            return (urwid.BoxAdapter(
                graphics_widget(img, image_format=self.timeline.tui.options.image_format, corner_radius=10,
                                colors=self.timeline.tui.options.colors), rows))
        else:
            placeholder = urwid.BoxAdapter(urwid.SolidFill(fill_char=" "), rows)
            self.status.placeholders.append(placeholder)
            if image_support_enabled():
                self.timeline.tui.async_load_image(self.timeline, self.status, path, len(self.status.placeholders) - 1)
            return placeholder

    def author_header(self, reblogged_by):
        avatar_url = self.status.original.data["account"]["avatar"]

        if avatar_url and image_support_enabled():
            aimg = self.image_widget(avatar_url, 2)

        account_color = ("highlight" if self.status.original.author.account in
                        self.timeline.tui.followed_accounts else "account")

        atxt = urwid.Pile([("pack", urwid.Text(("bold", self.status.original.author.display_name))),
                           ("pack", urwid.Text((account_color, self.status.original.author.account)))])

        if image_support_enabled():
            columns = urwid.Columns([aimg, ("weight", 9999, atxt)], dividechars=1, min_width=5)
        else:
            columns = urwid.Columns([("weight", 9999, atxt)], dividechars=1, min_width=5)

        return columns

    def content_generator(self, status, reblogged_by):
        if reblogged_by:
            reblogger_name = (reblogged_by.display_name
                              if reblogged_by.display_name
                              else reblogged_by.username)
            text = f"♺ {reblogger_name} boosted"
            yield urwid.Text(("dim", text))
            yield ("pack", urwid.AttrMap(urwid.Divider("-"), "dim"))

        yield self.author_header(reblogged_by)
        yield ("pack", urwid.Divider())

        if status.data["spoiler_text"]:
            yield ("pack", urwid.Text(status.data["spoiler_text"]))
            yield ("pack", urwid.Divider())

        # Show content warning
        if status.data["spoiler_text"] and not status.show_sensitive and not self.options.always_show_sensitive:
            yield ("pack", urwid.Text(("content_warning", "Marked as sensitive. Press S to view.")))
        else:
            if status.data["spoiler_text"]:
                yield ("pack", urwid.Text(("content_warning", "Marked as sensitive.")))

            content = status.original.translation if status.original.show_translation else status.data["content"]
            widgetlist = html_to_widgets(content)

            for line in widgetlist:
                yield (line)

            media = status.data["media_attachments"]
            if media:
                for m in media:
                    yield ("pack", urwid.AttrMap(urwid.Divider("-"), "dim"))
                    yield ("pack", urwid.Text([("bold", "Media attachment"), " (", m["type"], ")"]))
                    if m["description"]:
                        yield ("pack", urwid.Text(m["description"]))
                    if m["url"]:
                        if m["url"].lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp')):
                            yield urwid.Text("")
                            try:
                                aspect = float(m["meta"]["original"]["aspect"])
                            except Exception:
                                aspect = None
                            if image_support_enabled():
                                yield self.image_widget(m["url"], aspect=aspect)
                            yield urwid.Divider()
                        # video media may include a preview URL, show that as a fallback
                        elif m["preview_url"]:
                            if m["preview_url"].lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp')):
                                yield urwid.Text("")
                                try:
                                    aspect = float(m["meta"]["small"]["aspect"])
                                except Exception:
                                    aspect = None
                                if image_support_enabled():
                                    yield self.image_widget(m["preview_url"], aspect=aspect)
                                yield urwid.Divider()
                        yield ("pack", url_to_widget(m["url"]))

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

        yield ("pack", urwid.AttrWrap(urwid.Divider("-"), "dim"))

        translated_from = (
            language_name(status.original.translated_from)
            if status.original.show_translation and status.original.translated_from
            else None
        )

        visibility_colors = {
            "public": "visibility_public",
            "unlisted": "visibility_unlisted",
            "private": "visibility_private",
            "direct": "visibility_direct"
        }

        visibility = status.visibility.title()
        visibility_color = visibility_colors.get(status.visibility, "dim")

        yield ("pack", urwid.Text([
            ("status_detail_timestamp", f"{status.created_at.strftime('%Y-%m-%d %H:%M')} "),
            ("status_detail_timestamp",
             f"(edited {status.edited_at.strftime('%Y-%m-%d %H:%M')}) " if status.edited_at else ""),
            ("status_detail_bookmarked" if status.bookmarked else "dim", "b "),
            ("dim", f"⤶ {status.data['replies_count']} "),
            ("highlight" if status.reblogged else "dim", f"♺ {status.data['reblogs_count']} "),
            ("highlight" if status.favourited else "dim", f"★ {status.data['favourites_count']}"),
            (visibility_color, f" · {visibility}"),
            ("highlight", f" · Translated from {translated_from} " if translated_from else ""),
            ("dim", f" · {application}" if application else ""),
        ]))

        # Push things to bottom
        yield ("weight", 1, urwid.BoxAdapter(urwid.SolidFill(" "), 1))

    def build_linebox(self, contents):
        contents = urwid.Pile(list(contents))
        contents = urwid.Padding(contents, left=1, right=1)
        return RoundedLineBox(contents)

    def card_generator(self, card):
        yield urwid.Text(("card_title", card["title"].strip()))
        if card.get("author_name"):
            yield urwid.Text(["by ", ("card_author", card["author_name"].strip())])
        yield urwid.Text("")
        if card["description"]:
            yield urwid.Text(card["description"].strip())
            yield urwid.Text("")
        yield url_to_widget(card["url"])

        if card["image"] and image_support_enabled():
            if card["image"].lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp')):
                yield urwid.Text("")
                try:
                    aspect = int(card["width"]) / int(card["height"])
                except Exception:
                    aspect = None
                yield self.image_widget(card["image"], aspect=aspect)

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

        yield urwid.Text(("dim", status))


class StatusListItem(SelectableColumns):
    def __init__(self, status, relative_datetimes):
        edited_at = status.original.edited_at

        # TODO: hacky implementation to avoid creating conflicts for existing
        # pull requests, refactor when merged.
        created_at = (
            time_ago(status.created_at).ljust(3, " ")
            if relative_datetimes
            else status.created_at.strftime("%Y-%m-%d %H:%M")
        )

        edited_flag = "*" if edited_at else " "
        favourited = ("highlight", "★") if status.original.favourited else " "
        reblogged = ("highlight", "♺") if status.original.reblogged else " "
        is_reblog = ("dim", "♺") if status.reblog else " "
        is_reply = ("dim", "⤶ ") if status.original.in_reply_to else "  "

        return super().__init__([
            ("pack", SelectableText(("status_list_timestamp", created_at), wrap="clip")),
            ("pack", urwid.Text(("status_list_timestamp", edited_flag))),
            ("pack", urwid.Text(" ")),
            ("pack", urwid.Text(favourited)),
            ("pack", urwid.Text(" ")),
            ("pack", urwid.Text(reblogged)),
            ("pack", urwid.Text(" ")),
            urwid.Text(("status_list_account", status.original.account), wrap="clip"),
            ("pack", urwid.Text(is_reply)),
            ("pack", urwid.Text(is_reblog)),
            ("pack", urwid.Text(" ")),
        ])
