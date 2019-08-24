import logging
import urwid

from concurrent.futures import ThreadPoolExecutor

from toot import api

from .constants import PALETTE
from .entities import Status
from .timeline import Timeline

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

        # with open("tmp/statuses2.json", "w") as f:
        #     import json
        #     json.dump(data, f, indent=4)

        return [Status(s, self.app.instance) for s in data]

    def schedule_load_next(self):
        self.run_in_thread(self.load_statuses, done_callback=self.statuses_loaded_next)

    def statuses_loaded_initial(self, future):
        # TODO: handle errors in future
        self.body = Timeline(self, future.result())

        urwid.connect_signal(self.body, "status_focused",
            lambda _, args: self.status_focused(*args))
        urwid.connect_signal(self.body, "next",
            lambda *args: self.schedule_load_next())
        self.body.status_focused()  # Draw first status

    def statuses_loaded_next(self, future):
        # TODO: handle errors in future
        self.body.add_statuses(future.result())

    def status_focused(self, status, index, count):
        self.footer.set_status([
            ("footer_status_bold", "[home] "), status.id,
            " - status ", str(index + 1), " of ", str(count),
        ])

    def unhandled_input(self, key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
