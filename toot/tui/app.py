import logging
import urwid

from concurrent.futures import ThreadPoolExecutor

from toot import api, config, __version__
from toot.console import get_default_visibility
from toot.exceptions import ApiError

from .compose import StatusComposer
from .constants import PALETTE
from .entities import Status
from .overlays import ExceptionStackTrace, GotoMenu, Help, StatusSource, StatusLinks, StatusZoom
from .overlays import StatusDeleteConfirmation, Account
from .timeline import Timeline
from .utils import parse_content_links, show_media

logger = logging.getLogger(__name__)

urwid.set_encoding('UTF-8')


class Header(urwid.WidgetWrap):
    def __init__(self, app, user):
        self.app = app
        self.user = user

        self.text = urwid.Text("")
        self.cols = urwid.Columns([
            ("pack", urwid.Text(('header_bold', 'toot'))),
            ("pack", urwid.Text(('header', ' | {}@{}'.format(user.username, app.instance)))),
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

    def set_error_message(self, text):
        self.message.set_text(("footer_message_error", text))

    def clear_message(self):
        self.message.set_text("")


class TUI(urwid.Frame):
    """Main TUI frame."""

    @classmethod
    def create(cls, app, user, args):
        """Factory method, sets up TUI and an event loop."""

        tui = cls(app, user, args)
        loop = urwid.MainLoop(
            tui,
            palette=PALETTE,
            event_loop=urwid.AsyncioEventLoop(),
            unhandled_input=tui.unhandled_input,
        )
        tui.loop = loop

        return tui

    def __init__(self, app, user, args):
        self.app = app
        self.user = user
        self.args = args
        self.config = config.load_config()

        self.loop = None  # set in `create`
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.timeline_generator = api.home_timeline_generator(app, user, limit=40)

        # Show intro screen while toots are being loaded
        self.body = self.build_intro()
        self.header = Header(app, user)
        self.footer = Footer()
        self.footer.set_status("Loading...")

        # Default max status length, updated on startup
        self.max_toot_chars = 500

        self.timeline = None
        self.overlay = None
        self.exception = None
        self.can_translate = False

        super().__init__(self.body, header=self.header, footer=self.footer)

    def run(self):
        self.loop.set_alarm_in(0, lambda *args: self.async_load_instance())
        self.loop.set_alarm_in(0, lambda *args: self.async_load_followed_tags())
        self.loop.set_alarm_in(0, lambda *args: self.async_load_timeline(
            is_initial=True, timeline_name="home"))
        self.loop.run()
        self.executor.shutdown(wait=False)

    def build_intro(self):
        font = urwid.font.Thin6x6Font()

        # NB: Padding with width="clip" will convert the fixed BigText widget
        # to a flow widget so it can be used in a Pile.

        big_text = "Toot {}".format(__version__)
        big_text = urwid.BigText(("intro_bigtext", big_text), font)
        big_text = urwid.Padding(big_text, align="center", width="clip")

        intro = urwid.Pile([
            big_text,
            urwid.Divider(),
            urwid.Text([
                "Maintained by ",
                ("intro_smalltext", "@ihabunek"),
                " and contributors"
            ], align="center"),
            urwid.Divider(),
            urwid.Text(("intro_smalltext", "Loading toots..."), align="center"),
        ])

        return urwid.Filler(intro)

    def run_in_thread(self, fn, args=[], kwargs={}, done_callback=None, error_callback=None):
        """Runs `fn(*args, **kwargs)` asynchronously in a separate thread.

        On completion calls `done_callback` if `fn` exited cleanly, or
        `error_callback` if an exception was caught. Callback methods are
        invoked in the main thread, not the thread in which `fn` is executed.
        """

        def _default_error_callback(ex):
            self.exception = ex
            self.footer.set_error_message("An exception occurred, press E to view")

        _error_callback = error_callback or _default_error_callback

        def _done(future):
            try:
                result = future.result()
                if done_callback:
                    # Use alarm to invoke callback in main thread
                    self.loop.set_alarm_in(0, lambda *args: done_callback(result))
            except Exception as ex:
                exception = ex
                logger.exception(exception)
                self.loop.set_alarm_in(0, lambda *args: _error_callback(exception))

        future = self.executor.submit(fn, *args, **kwargs)
        future.add_done_callback(_done)
        return future

    def connect_default_timeline_signals(self, timeline):
        def _account(timeline, account_id):
            self.show_account(account_id)

        def _compose(*args):
            self.show_compose()

        def _delete(timeline, status):
            if status.is_mine:
                self.show_delete_confirmation(status)

        def _reply(timeline, status):
            self.show_compose(status)

        def _source(timeline, status):
            self.show_status_source(status)

        def _links(timeline, status):
            self.show_links(status)

        def _media(timeline, status):
            self.show_media(status)

        def _menu(timeline, status):
            self.show_context_menu(status)

        def _zoom(timeline, status_details):
            self.show_status_zoom(status_details)

        def _clear(*args):
            self.clear_screen()

        urwid.connect_signal(timeline, "account", _account)
        urwid.connect_signal(timeline, "bookmark", self.async_toggle_bookmark)
        urwid.connect_signal(timeline, "compose", _compose)
        urwid.connect_signal(timeline, "delete", _delete)
        urwid.connect_signal(timeline, "favourite", self.async_toggle_favourite)
        urwid.connect_signal(timeline, "focus", self.refresh_footer)
        urwid.connect_signal(timeline, "media", _media)
        urwid.connect_signal(timeline, "menu", _menu)
        urwid.connect_signal(timeline, "reblog", self.async_toggle_reblog)
        urwid.connect_signal(timeline, "reply", _reply)
        urwid.connect_signal(timeline, "source", _source)
        urwid.connect_signal(timeline, "links", _links)
        urwid.connect_signal(timeline, "zoom", _zoom)
        urwid.connect_signal(timeline, "translate", self.async_translate)
        urwid.connect_signal(timeline, "clear-screen", _clear)

    def build_timeline(self, name, statuses, local):
        def _close(*args):
            raise urwid.ExitMainLoop()

        def _next(*args):
            self.async_load_timeline(is_initial=False)

        def _thread(timeline, status):
            self.show_thread(status)

        def _toggle_save(timeline, status):
            if not timeline.name.startswith("#"):
                return
            hashtag = timeline.name[1:]
            assert isinstance(local, bool), local
            timelines = self.config.setdefault("timelines", {})
            if hashtag in timelines:
                del timelines[hashtag]
                self.footer.set_message("#{} unpinned".format(hashtag))
            else:
                timelines[hashtag] = {"local": local}
                self.footer.set_message("#{} pinned".format(hashtag))
            self.loop.set_alarm_in(5, lambda *args: self.footer.clear_message())
            config.save_config(self.config)

        timeline = Timeline(name, statuses, self.can_translate, self.followed_tags)

        self.connect_default_timeline_signals(timeline)
        urwid.connect_signal(timeline, "next", _next)
        urwid.connect_signal(timeline, "close", _close)
        urwid.connect_signal(timeline, "thread", _thread)
        urwid.connect_signal(timeline, "save", _toggle_save)

        return timeline

    def make_status(self, status_data):
        is_mine = self.user.username == status_data["account"]["acct"]
        return Status(status_data, is_mine, self.app.instance)

    def show_thread(self, status):
        def _close(*args):
            """When thread is closed, go back to the main timeline."""
            self.body = self.timeline
            self.body.refresh_status_details()
            self.refresh_footer(self.timeline)

        # This is pretty fast, so it's probably ok to block while context is
        # loaded, can be made async later if needed
        context = api.context(self.app, self.user, status.original.id)
        ancestors = [self.make_status(s) for s in context["ancestors"]]
        descendants = [self.make_status(s) for s in context["descendants"]]
        statuses = ancestors + [status] + descendants
        focus = len(ancestors)

        timeline = Timeline("thread", statuses, self.can_translate,
                            self.followed_tags, focus, is_thread=True)

        self.connect_default_timeline_signals(timeline)
        urwid.connect_signal(timeline, "close", _close)

        self.body = timeline
        self.refresh_footer(timeline)

    def async_load_timeline(self, is_initial, timeline_name=None, local=None):
        """Asynchronously load a list of statuses."""

        def _load_statuses():
            self.footer.set_message("Loading statuses...")
            try:
                data = next(self.timeline_generator)
            except StopIteration:
                return []
            finally:
                self.footer.clear_message()

            return [self.make_status(s) for s in data]

        def _done_initial(statuses):
            """Process initial batch of statuses, construct a Timeline."""
            self.timeline = self.build_timeline(timeline_name, statuses, local)
            self.timeline.refresh_status_details()  # Draw first status
            self.refresh_footer(self.timeline)
            self.body = self.timeline

        def _done_next(statuses):
            """Process sequential batch of statuses, adds statuses to the
            existing timeline."""
            self.timeline.append_statuses(statuses)

        return self.run_in_thread(_load_statuses,
            done_callback=_done_initial if is_initial else _done_next)

    def async_load_instance(self):
        """
        Attempt to update max_toot_chars from instance data.
        Does not work on vanilla Mastodon, works on Pleroma.
        See: https://github.com/tootsuite/mastodon/issues/4915

        Also attempt to update translation flag from instance
        data. Translation is only present on Mastodon 4+ servers
        where the administrator has enabled this feature.
        See: https://github.com/mastodon/mastodon/issues/19328
        """
        def _load_instance():
            return api.get_instance(self.app.instance)

        def _done(instance):
            if "max_toot_chars" in instance:
                self.max_toot_chars = instance["max_toot_chars"]

            if "translation" in instance:
                # instance is advertising translation service
                self.can_translate = instance["translation"]["enabled"]
            elif "version" in instance:
                # fallback check:
                # get the major version number of the server
                # this works for Mastodon and Pleroma version strings
                # Mastodon versions < 4 do not have translation service
                # Revisit this logic if Pleroma implements translation
                ch = instance["version"][0]
                self.can_translate = int(ch) > 3 if ch.isnumeric() else False

        return self.run_in_thread(_load_instance, done_callback=_done)

    def async_load_followed_tags(self):
        def _load_tag_list():
            try:
                return api.followed_tags(self.app, self.user)
            except ApiError:
                # not supported by all Mastodon servers so fail silently if necessary
                return []

        def _done_tag_list(tags):
            if len(tags) > 0:
                self.followed_tags = [t["name"] for t in tags]
            else:
                self.followed_tags = []

        self.run_in_thread(_load_tag_list, done_callback=_done_tag_list)

    def refresh_footer(self, timeline):
        """Show status details in footer."""
        status, index, count = timeline.get_focused_status_with_counts()
        self.footer.set_status([
            ("footer_status_bold", "[{}] ".format(timeline.name)),
        ] + ([status.id, " - status ", str(index + 1), " of ", str(count)]
            if status else ["no focused status"]))

    def show_status_source(self, status):
        self.open_overlay(
            widget=StatusSource(status),
            title="Status source",
        )

    def clear_screen(self):
        self.loop.screen.clear()

    def show_links(self, status):
        links = parse_content_links(status.data["content"]) if status else []
        post_attachments = status.data["media_attachments"] or []
        reblog_attachments = (status.data["reblog"]["media_attachments"] if status.data["reblog"] else None) or []

        for a in post_attachments + reblog_attachments:
            url = a["remote_url"] or a["url"]
            links.append((url, a["description"] if a["description"] else url))

        def _clear(*args):
            self.clear_screen()

        if links:
            sl_widget = StatusLinks(links)
            urwid.connect_signal(sl_widget, "clear-screen", _clear)
            self.open_overlay(
                widget=sl_widget,
                title="Status links",
                options={"height": len(links) + 2},
            )

    def show_status_zoom(self, status_details):
        self.open_overlay(
            widget=StatusZoom(status_details),
            title="Status zoom",
        )

    def show_exception(self, exception):
        self.open_overlay(
            widget=ExceptionStackTrace(exception),
            title="Unhandled Exception",
        )

    def show_compose(self, in_reply_to=None):
        def _close(*args):
            self.close_overlay()

        def _post(timeline, *args):
            self.post_status(*args)

        composer = StatusComposer(self.max_toot_chars, self.user.username, in_reply_to)
        urwid.connect_signal(composer, "close", _close)
        urwid.connect_signal(composer, "post", _post)
        self.open_overlay(composer, title="Compose status")

    def show_goto_menu(self):
        user_timelines = self.config.get("timelines", {})
        menu = GotoMenu(user_timelines)
        urwid.connect_signal(menu, "home_timeline",
            lambda x: self.goto_home_timeline())
        urwid.connect_signal(menu, "public_timeline",
            lambda x, local: self.goto_public_timeline(local))
        urwid.connect_signal(menu, "bookmark_timeline",
            lambda x, local: self.goto_bookmarks())

        urwid.connect_signal(menu, "hashtag_timeline",
            lambda x, tag, local: self.goto_tag_timeline(tag, local=local))

        self.open_overlay(menu, title="Go to", options=dict(
            align="center", width=("relative", 60),
            valign="middle", height=10 + len(user_timelines),
        ))

    def show_help(self):
        self.open_overlay(Help(), title="Help")

    def goto_home_timeline(self):
        self.timeline_generator = api.home_timeline_generator(
            self.app, self.user, limit=40)
        promise = self.async_load_timeline(is_initial=True, timeline_name="home")
        promise.add_done_callback(lambda *args: self.close_overlay())

    def goto_public_timeline(self, local):
        self.timeline_generator = api.public_timeline_generator(
            self.app, self.user, local=local, limit=40)
        promise = self.async_load_timeline(is_initial=True, timeline_name="public")
        promise.add_done_callback(lambda *args: self.close_overlay())

    def goto_bookmarks(self):
        self.timeline_generator = api.bookmark_timeline_generator(
            self.app, self.user, limit=40)
        promise = self.async_load_timeline(is_initial=True, timeline_name="bookmarks")
        promise.add_done_callback(lambda *args: self.close_overlay())

    def goto_tag_timeline(self, tag, local):
        self.timeline_generator = api.tag_timeline_generator(
            self.app, self.user, tag, local=local, limit=40)
        promise = self.async_load_timeline(
            is_initial=True, timeline_name="#{}".format(tag), local=local,
        )
        promise.add_done_callback(lambda *args: self.close_overlay())

    def show_media(self, status):
        urls = [m["url"] for m in status.original.data["media_attachments"]]
        if urls:
            show_media(urls)

    def show_context_menu(self, status):
        # TODO: show context menu
        pass

    def show_delete_confirmation(self, status):
        def _delete(widget):
            promise = self.async_delete_status(self.timeline, status)
            promise.add_done_callback(lambda *args: self.close_overlay())

        def _close(widget):
            self.close_overlay()

        widget = StatusDeleteConfirmation(status)
        urwid.connect_signal(widget, "close", _close)
        urwid.connect_signal(widget, "delete", _delete)
        self.open_overlay(widget, title="Delete status?", options=dict(
            align="center", width=("relative", 60),
            valign="middle", height=5,
        ))

    def post_status(self, content, warning, visibility, in_reply_to_id):
        data = api.post_status(self.app, self.user, content,
            spoiler_text=warning,
            visibility=visibility,
            in_reply_to_id=in_reply_to_id)
        status = self.make_status(data)

        # TODO: fetch new items from the timeline?

        self.footer.set_message("Status posted {} \\o/".format(status.id))
        self.close_overlay()

    def show_account(self, account_id):
        account = api.whois(self.app, self.user, account_id)
        self.open_overlay(
            widget=Account(account),
            title="Account",
        )

    def async_toggle_favourite(self, timeline, status):
        def _favourite():
            logger.info("Favouriting {}".format(status))
            api.favourite(self.app, self.user, status.id)

        def _unfavourite():
            logger.info("Unfavouriting {}".format(status))
            api.unfavourite(self.app, self.user, status.id)

        def _done(loop):
            # Create a new Status with flipped favourited flag
            new_data = status.data
            new_data["favourited"] = not status.favourited
            new_status = self.make_status(new_data)
            timeline.update_status(new_status)

        self.run_in_thread(
            _unfavourite if status.favourited else _favourite,
            done_callback=_done
        )

    def async_toggle_reblog(self, timeline, status):
        def _reblog():
            logger.info("Reblogging {}".format(status))
            api.reblog(self.app, self.user, status.id, visibility=get_default_visibility())

        def _unreblog():
            logger.info("Unreblogging {}".format(status))
            api.unreblog(self.app, self.user, status.id)

        def _done(loop):
            # Create a new Status with flipped reblogged flag
            new_data = status.data
            new_data["reblogged"] = not status.reblogged
            new_status = self.make_status(new_data)
            timeline.update_status(new_status)

        # Check if status is rebloggable
        no_reblog_because_private = status.visibility == "private" and not status.is_mine
        no_reblog_because_direct = status.visibility == "direct"
        if no_reblog_because_private or no_reblog_because_direct:
            self.footer.set_error_message("You may not reblog this {} status".format(status.visibility))
            return

        self.run_in_thread(
            _unreblog if status.reblogged else _reblog,
            done_callback=_done
        )

    def async_translate(self, timeline, status):
        def _translate():
            logger.info("Translating {}".format(status))
            self.footer.set_message("Translating status {}".format(status.id))

            try:
                response = api.translate(self.app, self.user, status.id)
                if response["content"]:
                    self.footer.set_message("Status translated")
                else:
                    self.footer.set_error_message("Server returned empty translation")
                    response = None
            except Exception:
                response = None
                self.footer.set_error_message("Translate server error")

            self.loop.set_alarm_in(3, lambda *args: self.footer.clear_message())
            return response

        def _done(response):
            if response is not None:
                status.translation = response["content"]
                status.translated_from = response["detected_source_language"]
                status.show_translation = True
                timeline.update_status(status)

        # If already translated, toggle showing translation
        if status.translation:
            status.show_translation = not status.show_translation
            timeline.update_status(status)
        else:
            self.run_in_thread(_translate, done_callback=_done)

    def async_toggle_bookmark(self, timeline, status):
        def _bookmark():
            logger.info("Bookmarking {}".format(status))
            api.bookmark(self.app, self.user, status.id)

        def _unbookmark():
            logger.info("Unbookmarking {}".format(status))
            api.unbookmark(self.app, self.user, status.id)

        def _done(loop):
            # Create a new Status with flipped bookmarked flag
            new_data = status.data
            new_data["bookmarked"] = not status.bookmarked
            new_status = self.make_status(new_data)
            timeline.update_status(new_status)

        self.run_in_thread(
            _unbookmark if status.bookmarked else _bookmark,
            done_callback=_done
        )

    def async_delete_status(self, timeline, status):
        def _delete():
            api.delete_status(self.app, self.user, status.id)

        def _done(loop):
            timeline.remove_status(status)

        return self.run_in_thread(_delete, done_callback=_done)

    # --- Overlay handling -----------------------------------------------------

    default_overlay_options = dict(
        align="center", width=("relative", 80),
        valign="middle", height=("relative", 80),
    )

    def open_overlay(self, widget, options={}, title=""):
        top_widget = urwid.LineBox(widget, title=title)
        bottom_widget = self.body

        _options = self.default_overlay_options.copy()
        _options.update(options)

        self.overlay = urwid.Overlay(
            top_widget,
            bottom_widget,
            **_options
        )
        self.body = self.overlay

    def close_overlay(self):
        self.body = self.overlay.bottom_w
        self.overlay = None

    # --- Keys -----------------------------------------------------------------

    def unhandled_input(self, key):
        # TODO: this should not be in unhandled input
        if key in ('e', 'E'):
            if self.exception:
                self.show_exception(self.exception)

        elif key in ('g', 'G'):
            if not self.overlay:
                self.show_goto_menu()

        elif key in ('h', 'H'):
            if not self.overlay:
                self.show_help()

        elif key == ',':
            if not self.overlay:
                self.timeline_generator = api.home_timeline_generator(
                    self.app, self.user, limit=40)
                self.async_load_timeline(is_initial=True, timeline_name=self.timeline.name)

        elif key == 'esc':
            if self.overlay:
                self.close_overlay()
            elif self.timeline.name != "home":
                # similar to goto_home_timeline() but without handling overlay (absent here)
                self.timeline_generator = api.home_timeline_generator(
                    self.app, self.user, limit=40)
                self.async_load_timeline(is_initial=True, timeline_name="home")

        elif key in ('q', 'Q'):
            if self.overlay:
                self.close_overlay()
            else:
                raise urwid.ExitMainLoop()
