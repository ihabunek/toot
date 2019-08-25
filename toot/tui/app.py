import json
import logging
import urwid

from concurrent.futures import ThreadPoolExecutor

from toot import api

from .constants import PALETTE
from .entities import Status
from .timeline import Timeline
from .widgets import SelectableText

logger = logging.getLogger(__name__)


class Header(urwid.WidgetWrap):
    def __init__(self, app, user):
        self.app = app
        self.user = user

        self.text = urwid.Text("")
        self.cols = urwid.Columns([
            ("pack", urwid.Text(('header_bold', 'toot'))),
            ("pack", urwid.Text(('header', f' | {user.username}@{app.instance}'))),
            ("pack", self.text),
        ])

        widget = urwid.AttrMap(self.cols, 'header')
        widget = urwid.Padding(widget)
        self._wrapped_widget = widget

    def clear_text(self, text):
        self.text.set_text("")

    def set_text(self, text):
        self.text.set_text(" | " + text)


class Footer(urwid.Pile):
    def __init__(self):
        self.status = urwid.Text("")
        self.message = urwid.Text("")

        return super().__init__([
            urwid.AttrMap(self.status, "footer_status"),
            urwid.AttrMap(self.message, "footer_message"),
        ])

    def set_status(self, text):
        self.status.set_text(text)

    def clear_status(self, text):
        self.status.set_text("")

    def set_message(self, text):
        self.message.set_text(text)

    def clear_message(self):
        self.message.set_text("")


class TUI(urwid.Frame):
    """Main TUI frame."""

    @classmethod
    def create(cls, app, user):
        """Factory method, sets up TUI and an event loop."""

        tui = cls(app, user)
        loop = urwid.MainLoop(
            tui,
            palette=PALETTE,
            event_loop=urwid.AsyncioEventLoop(),
            unhandled_input=tui.unhandled_input,
        )
        tui.loop = loop

        return tui

    def __init__(self, app, user):
        self.app = app
        self.user = user

        self.loop = None  # set in `create`
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.timeline_generator = api.home_timeline_generator(app, user, limit=40)
        # self.timeline_generator = api.public_timeline_generator(app.instance, local=False, limit=40)

        self.body = urwid.Filler(urwid.Text("Loading toots...", align="center"))
        self.header = Header(app, user)
        self.footer = Footer()
        self.footer.set_status("Loading...")

        self.timeline = None
        self.overlay = None

        super().__init__(self.body, header=self.header, footer=self.footer)

    def run(self):
        self.loop.set_alarm_in(0, self.schedule_load_statuses)
        self.loop.run()
        self.executor.shutdown(wait=False)

    def run_in_thread(self, fn, args=[], kwargs={}, done_callback=None):
        future = self.executor.submit(fn)
        if done_callback:
            future.add_done_callback(done_callback)

    def schedule_load_statuses(self, *args):
        self.run_in_thread(self.load_statuses, done_callback=self.statuses_loaded_initial)

    def load_statuses(self):
        self.footer.set_message("Loading statuses...")
        try:
            data = next(self.timeline_generator)
        except StopIteration:
            return []
        finally:
            self.footer.clear_message()

        # # FIXME: REMOVE DEBUGGING
        # with open("tmp/statuses2.json", "w") as f:
        #     import json
        #     json.dump(data, f, indent=4)

        return [Status(s, self.app.instance) for s in data]

    def schedule_load_next(self):
        self.run_in_thread(self.load_statuses, done_callback=self.statuses_loaded_next)

    def statuses_loaded_initial(self, future):
        # TODO: handle errors in future
        self.timeline = Timeline(self, future.result())

        urwid.connect_signal(self.timeline, "status_focused",
            lambda _, args: self.status_focused(*args))
        urwid.connect_signal(self.timeline, "next",
            lambda *args: self.schedule_load_next())
        self.timeline.status_focused()  # Draw first status
        self.body = self.timeline

    def statuses_loaded_next(self, future):
        # TODO: handle errors in future
        self.timeline.add_statuses(future.result())

    def status_focused(self, status, index, count):
        self.footer.set_status([
            ("footer_status_bold", "[home] "), status.id,
            " - status ", str(index + 1), " of ", str(count),
        ])

    def show_status_source(self, status):
        self.open_overlay(
            widget=StatusSource(status),
            title="Status source",
            options={
                "align": 'center',
                "width": ('relative', 80),
                "valign": 'middle',
                "height": ('relative', 80),
            },
        )

    # --- Overlay handling -----------------------------------------------------

    def open_overlay(self, widget, options={}, title=""):
        top_widget = urwid.LineBox(widget, title=title)
        bottom_widget = self.body

        self.overlay = urwid.Overlay(
            top_widget,
            bottom_widget,
            **options
        )
        self.body = self.overlay

    def close_overlay(self):
        self.body = self.overlay.bottom_w
        self.overlay = None

    # --- Keys -----------------------------------------------------------------

    def unhandled_input(self, key):
        if key in ('q', 'Q'):
            if self.overlay:
                self.close_overlay()
            else:
                raise urwid.ExitMainLoop()


class StatusSource(urwid.ListBox):
    """Shows status data, as returned by the server, as formatted JSON."""
    def __init__(self, status):
        source = json.dumps(status.data, indent=4)
        lines = source.splitlines()
        focus_map = {None: "blue_selected"}
        walker = urwid.SimpleFocusListWalker([
            urwid.AttrMap(SelectableText(line), None, focus_map)
            for line in lines
        ])
        super().__init__(walker)
