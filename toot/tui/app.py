import logging
import subprocess
import urwid


from concurrent.futures import ThreadPoolExecutor
from typing import NamedTuple, Optional
from datetime import datetime, timezone

from toot import api, config, __version__, settings
from toot import App, User
from toot.cli import get_default_visibility
from toot.utils.datetime import parse_datetime

from .compose import StatusComposer
from .constants import PALETTE
from .entities import Status
from .images import TuiScreen, load_image
from .overlays import ExceptionStackTrace, GotoMenu, Help, StatusSource, StatusLinks, StatusZoom
from .overlays import StatusDeleteConfirmation, Account
from .poll import Poll
from .timeline import Timeline
from .utils import get_max_toot_chars, parse_content_links, copy_to_clipboard, LRUCache
from .widgets import ModalBox, RoundedLineBox

logger = logging.getLogger(__name__)

urwid.set_encoding('UTF-8')


DEFAULT_MAX_TOOT_CHARS = 500


class TuiOptions(NamedTuple):
    colors: int
    media_viewer: Optional[str]
    always_show_sensitive: bool
    relative_datetimes: bool
    cache_size: int
    default_visibility: Optional[str]
    image_format: Optional[str]
    show_display_names: bool


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
    loop: urwid.MainLoop
    screen: urwid.BaseScreen

    @staticmethod
    def create(app: App, user: User, options: TuiOptions):
        """Factory method, sets up TUI and an event loop."""
        screen = TuiScreen()
        screen.set_terminal_properties(options.colors)

        tui = TUI(app, user, screen, options)

        palette = PALETTE.copy()
        overrides = settings.get_setting("tui.palette", dict, {})
        for name, styles in overrides.items():
            palette.append(tuple([name] + styles))

        loop = urwid.MainLoop(
            tui,
            palette=palette,
            event_loop=urwid.AsyncioEventLoop(),
            unhandled_input=tui.unhandled_input,
            screen=screen,
        )
        tui.loop = loop

        return tui

    def __init__(self, app, user, screen, options: TuiOptions):
        self.app = app
        self.user = user
        self.config = config.load_config()
        self.options = options

        self.loop = None  # late init, set in `create`
        self.screen = screen
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.timeline_generator = api.home_timeline_generator(app, user, limit=40)

        # Show intro screen while toots are being loaded
        self.body = self.build_intro()
        self.header = Header(app, user)
        self.footer = Footer()
        self.footer.set_status("Loading...")

        # Default max status length, updated on startup
        self.max_toot_chars = DEFAULT_MAX_TOOT_CHARS

        self.timeline = None
        self.overlay = None
        self.exception = None
        self.can_translate = False
        self.account = None
        self.followed_accounts = []
        self.preferences = {}

        if self.options.cache_size:
            self.cache_max = 1024 * 1024 * self.options.cache_size
        else:
            self.cache_max = 1024 * 1024 * 10  # default 10MB

        super().__init__(self.body, header=self.header, footer=self.footer)

    def run(self):
        self.loop.set_alarm_in(0, lambda *args: self.async_load_account())
        self.loop.set_alarm_in(0, lambda *args: self.async_load_instance())
        self.loop.set_alarm_in(0, lambda *args: self.async_load_preferences())
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

    def run_in_thread(self, fn, done_callback=None, error_callback=None):
        """Runs `fn` asynchronously in a separate thread.

        On completion calls `done_callback` if `fn` exited cleanly, or
        `error_callback` if an exception was caught. Callback methods are
        invoked in the main thread, not the thread in which `fn` is executed.
        """

        def _default_error_callback(ex):
            self.exception = ex
            self.footer.set_error_message("An exception occurred, press X to view")

        _error_callback = error_callback or _default_error_callback

        def _done(future):
            try:
                result = future.result()
                if done_callback:
                    # Use alarm to invoke callback in main thread
                    self.loop.set_alarm_in(0, lambda *args: done_callback(result))
            except Exception as ex:
                exception = ex
                self.loop.set_alarm_in(0, lambda *args: _error_callback(exception))

        # TODO: replace by `self.loop.event_loop.run_in_executor` at some point
        # Added in https://github.com/urwid/urwid/issues/575
        # Not yet released at the time of this comment
        future = self.loop.event_loop._loop.run_in_executor(self.executor, fn)
        future.add_done_callback(_done)
        return future

    def connect_default_timeline_signals(self, timeline):
        urwid.connect_signal(timeline, "focus", self.refresh_footer)

    def build_timeline(self, name, statuses, local):
        def _close(*args):
            raise urwid.ExitMainLoop()

        def _next(*args):
            self.async_load_timeline(is_initial=False)

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

        timeline = Timeline(self, name, statuses)

        self.connect_default_timeline_signals(timeline)
        urwid.connect_signal(timeline, "next", _next)
        urwid.connect_signal(timeline, "close", _close)
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
        context = api.context(self.app, self.user, status.original.id).json()
        ancestors = [self.make_status(s) for s in context["ancestors"]]
        descendants = [self.make_status(s) for s in context["descendants"]]
        statuses = ancestors + [status] + descendants
        focus = len(ancestors)

        timeline = Timeline(self, "thread", statuses, focus=focus, is_thread=True)

        self.connect_default_timeline_signals(timeline)
        urwid.connect_signal(timeline, "close", _close)
        self.body = timeline
        timeline.refresh_status_details()
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
            return api.get_instance(self.app.base_url).json()

        def _done(instance):
            self.max_toot_chars = get_max_toot_chars(instance, DEFAULT_MAX_TOOT_CHARS)
            logger.info(f"Max toot chars set to: {self.max_toot_chars}")

            if "translation" in instance:
                # instance is advertising translation service
                self.can_translate = instance["translation"]["enabled"]
            elif "version" in instance:
                # fallback check:
                # get the major version number of the server
                # this works for Mastodon and Pleroma version strings
                # Mastodon versions < 4 do not have translation service
                # If the version is missing, assume 0 as a fallback
                # Revisit this logic if Pleroma implements translation
                version = instance["version"]
                ch = "0" if not version else version[0]
                self.can_translate = int(ch) > 3 if ch.isnumeric() else False

        return self.run_in_thread(_load_instance, done_callback=_done)

    def async_load_preferences(self):
        """
        Attempt to update user preferences from instance.
        https://docs.joinmastodon.org/methods/preferences/
        """
        def _load_preferences():
            return api.get_preferences(self.app, self.user).json()

        def _done(preferences):
            self.preferences = preferences

        return self.run_in_thread(_load_preferences, done_callback=_done)

    def async_load_account(self):
        def _load_account():
            return api.verify_credentials(self.app, self.user).json()

        def _done_account(account):
            self.account = account
            self.loop.set_alarm_in(0, lambda *_: self.async_load_followed_accounts())

        self.run_in_thread(_load_account, done_callback=_done_account)

    def async_load_followed_accounts(self):
        def _load_accounts():
            try:
                if self.account:
                    return api.following(self.app, self.user, self.account["id"])
                return []
            except Exception:
                # not supported by all Mastodon servers so fail silently if necessary
                return []

        def _done_accounts(accounts):
            self.followed_accounts = {a["acct"] for a in accounts}

        self.run_in_thread(_load_accounts, done_callback=_done_accounts)

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
        self.screen.clear()

    def show_links(self, status):
        links = parse_content_links(status.original.data["content"]) if status else []
        post_attachments = status.original.data["media_attachments"] or []
        reblog_attachments = (status.data["reblog"]["media_attachments"] if status.data["reblog"] else None) or []

        for a in post_attachments + reblog_attachments:
            url = a["remote_url"] or a["url"]
            links.append((url, a["description"] if a["description"] else url))

        def _clear(*args):
            self.clear_screen()

        if links:
            links = list(set(links))  # deduplicate links
            links = sorted(links, key=lambda link: link[0])  # sort alphabetically by URL
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

        # If the user specified --default-visibility, use that; otherwise,
        # try to use the server-side default visibility.  If that fails, fall
        # back to get_default_visibility().
        visibility = (self.options.default_visibility or
                      self.preferences.get('posting:default:visibility',
                                           get_default_visibility()))

        composer = StatusComposer(self.max_toot_chars, self.user.username,
                                  visibility, in_reply_to)
        urwid.connect_signal(composer, "close", _close)
        urwid.connect_signal(composer, "post", _post)
        self.open_overlay(composer, title="Compose status")

    def async_edit(self, status):
        def _fetch_source():
            return api.fetch_status_source(self.app, self.user, status.id).json()

        def _done(source):
            self.close_overlay()
            self.show_edit(status, source)

        please_wait = ModalBox("Loading status...")
        self.open_overlay(please_wait)

        self.run_in_thread(_fetch_source, done_callback=_done)

    def show_edit(self, status, source):
        def _close(*args):
            self.close_overlay()

        def _edit(timeline, *args):
            self.edit_status(status, *args)

        composer = StatusComposer(self.max_toot_chars, self.user.username,
                                  visibility=None, edit=status, source=source)
        urwid.connect_signal(composer, "close", _close)
        urwid.connect_signal(composer, "post", _edit)
        self.open_overlay(composer, title="Edit status")

    def show_goto_menu(self):
        user_timelines = self.config.get("timelines", {})
        user_lists = api.get_lists(self.app, self.user) or []

        menu = GotoMenu(user_timelines, user_lists)
        urwid.connect_signal(menu, "home_timeline",
            lambda x: self.goto_home_timeline())
        urwid.connect_signal(menu, "public_timeline",
            lambda x, local: self.goto_public_timeline(local))
        urwid.connect_signal(menu, "bookmark_timeline",
            lambda x, local: self.goto_bookmarks())
        urwid.connect_signal(menu, "notification_timeline",
            lambda x, local: self.goto_notifications())
        urwid.connect_signal(menu, "conversation_timeline",
            lambda x, local: self.goto_conversations())
        urwid.connect_signal(menu, "personal_timeline",
            lambda x, local: self.goto_personal_timeline())
        urwid.connect_signal(menu, "hashtag_timeline",
            lambda x, tag, local: self.goto_tag_timeline(tag, local=local))
        urwid.connect_signal(menu, "list_timeline",
            lambda x, list_item: self.goto_list_timeline(list_item))

        self.open_overlay(menu, title="Go to", options=dict(
            align="center", width=("relative", 60),
            valign="middle", height=18 + len(user_timelines) + len(user_lists),
        ))

    def show_help(self):
        self.open_overlay(Help(), title="Help")

    def show_poll(self, status):
        self.open_overlay(
            widget=Poll(self.app, self.user, status),
            title="Poll",
        )

    def goto_home_timeline(self):
        self.timeline_generator = api.home_timeline_generator(
            self.app, self.user, limit=40)
        promise = self.async_load_timeline(is_initial=True, timeline_name="home")
        promise.add_done_callback(lambda *args: self.close_overlay())

    def goto_public_timeline(self, local):
        self.timeline_generator = api.public_timeline_generator(
            self.app, self.user, local=local, limit=40)
        timeline_name = "local public" if local else "global public"
        promise = self.async_load_timeline(is_initial=True, timeline_name=timeline_name)
        promise.add_done_callback(lambda *args: self.close_overlay())

    def goto_bookmarks(self):
        self.timeline_generator = api.bookmark_timeline_generator(
            self.app, self.user, limit=40)
        promise = self.async_load_timeline(is_initial=True, timeline_name="bookmarks")
        promise.add_done_callback(lambda *args: self.close_overlay())

    def goto_notifications(self):
        self.timeline_generator = api.notification_timeline_generator(
            self.app, self.user, limit=40)
        promise = self.async_load_timeline(is_initial=True, timeline_name="notifications")
        promise.add_done_callback(lambda *args: self.close_overlay())

    def goto_conversations(self):
        self.timeline_generator = api.conversation_timeline_generator(
            self.app, self.user, limit=40
        )
        promise = self.async_load_timeline(
            is_initial=True, timeline_name="conversations"
        )
        promise.add_done_callback(lambda *args: self.close_overlay())

    def goto_tag_timeline(self, tag, local):
        self.timeline_generator = api.tag_timeline_generator(
            self.app, self.user, tag, local=local, limit=40)
        promise = self.async_load_timeline(
            is_initial=True, timeline_name="#{}".format(tag), local=local,
        )
        promise.add_done_callback(lambda *args: self.close_overlay())

    def goto_personal_timeline(self):
        if not self.account:
            return
        self.timeline_generator = api.account_timeline_generator_by_id(
            self.app, self.user, self.account["id"], reblogs=True, limit=40)
        promise = self.async_load_timeline(
            is_initial=True, timeline_name=f"personal {self.user.username}")
        promise.add_done_callback(lambda *args: self.close_overlay())

    def goto_list_timeline(self, list_item):
        self.timeline_generator = api.timeline_list_generator(
            self.app, self.user, list_item['id'], limit=40)
        promise = self.async_load_timeline(
            is_initial=True, timeline_name=f"\N{clipboard}{list_item['title']}")
        promise.add_done_callback(lambda *args: self.close_overlay())

    def show_media(self, status):
        urls = [m["url"] for m in status.original.data["media_attachments"]]
        if not urls:
            return

        media_viewer = self.options.media_viewer
        if media_viewer:
            try:
                command = media_viewer.split()
                command.extend(urls)
                subprocess.run(command)
            except FileNotFoundError:
                self.footer.set_error_message(f"Media viewer not found: '{media_viewer}'")
            except Exception as ex:
                self.exception = ex
                self.footer.set_error_message("Failed invoking media viewer. Press X to see exception.")
        else:
            self.footer.set_error_message("Media viewer not configured")

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
            align="center", width=30,
            valign="middle", height=4,
        ))

    def post_status(self, content, warning, visibility, in_reply_to_id):
        data = api.post_status(
            self.app,
            self.user,
            content,
            spoiler_text=warning,
            visibility=visibility,
            in_reply_to_id=in_reply_to_id
        ).json()

        status = self.make_status(data)

        # TODO: fetch new items from the timeline?

        self.footer.set_message("Status posted {} \\o/".format(status.id))
        self.close_overlay()

    def edit_status(self, status, content, warning, visibility, in_reply_to_id):
        # We don't support editing polls (yet), so to avoid losing the poll
        # data from the original toot, copy it to the edit request.
        poll_args = {}
        poll = status.original.data.get('poll', None)

        if poll is not None:
            poll_args['poll_options'] = [o['title'] for o in poll['options']]
            poll_args['poll_multiple'] = poll['multiple']

            # Convert absolute expiry time into seconds from now.
            expires_at = parse_datetime(poll['expires_at'])
            expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())
            poll_args['poll_expires_in'] = expires_in

            if 'hide_totals' in poll:
                poll_args['poll_hide_totals'] = poll['hide_totals']

        data = api.edit_status(
            self.app,
            self.user,
            status.id,
            content,
            spoiler_text=warning,
            visibility=visibility,
            **poll_args
        ).json()

        new_status = self.make_status(data)

        self.footer.set_message("Status edited {} \\o/".format(status.id))
        self.close_overlay()

        if self.timeline is not None:
            self.timeline.update_status(new_status)

    def show_account(self, account_id):
        account = api.whois(self.app, self.user, account_id)
        relationship = api.get_relationship(self.app, self.user, account_id)
        self.open_overlay(
            widget=Account(self.app, self.user, account, relationship, self.options),
            title="Account",
        )

    def async_toggle_favourite(self, timeline, status):
        def _favourite():
            api.favourite(self.app, self.user, status.id)

        def _unfavourite():
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
            api.reblog(self.app, self.user, status.original.id, visibility=get_default_visibility())

        def _unreblog():
            api.unreblog(self.app, self.user, status.original.id)

        def _done(loop):
            # Create a new Status with flipped reblogged flag
            new_data = status.data
            new_status = self.make_status(new_data)
            new_status.original.reblogged = not status.original.reblogged
            timeline.update_status(new_status)

        # Check if status is rebloggable
        no_reblog_because_private = status.visibility == "private" and not status.is_mine
        no_reblog_because_direct = status.visibility == "direct"
        if no_reblog_because_private or no_reblog_because_direct:
            self.footer.set_error_message("You may not reblog this {} status".format(status.visibility))
            return

        self.run_in_thread(
            _unreblog if status.original.reblogged else _reblog,
            done_callback=_done
        )

    def async_translate(self, timeline, status):
        def _translate():
            self.footer.set_message("Translating status {}".format(status.original.id))

            try:
                response = api.translate(self.app, self.user, status.original.id)
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
                status.original.translation = response["content"]
                status.original.translated_from = response["detected_source_language"]
                status.original.show_translation = True
                timeline.update_status(status)

        # If already translated, toggle showing translation
        if status.original.translation:
            status.original.show_translation = not status.original.show_translation
            timeline.update_status(status)
        else:
            self.run_in_thread(_translate, done_callback=_done)

    def async_toggle_bookmark(self, timeline, status):
        def _bookmark():
            api.bookmark(self.app, self.user, status.id)

        def _unbookmark():
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

    def async_load_image(self, timeline, status, path, placeholder_index):
        def _load():
            # don't bother loading images for statuses we are not viewing now
            if timeline.get_focused_status().id != status.id:
                return

            if not hasattr(timeline, "images"):
                timeline.images = LRUCache(cache_max_bytes=self.cache_max)

            img = load_image(path)
            if img:
                timeline.images[str(hash(path))] = img

        def _done(loop):
            # don't bother loading images for statuses we are not viewing now
            if timeline.get_focused_status().id != status.id:
                return
            timeline.update_status_image(status, path, placeholder_index)

        return self.run_in_thread(_load, done_callback=_done)

    def copy_status(self, status):
        # TODO: copy a better version of status content
        # including URLs
        copy_to_clipboard(self.screen, status.original.data["content"])
        self.footer.set_message(f"Status {status.original.id} copied")

    # --- Overlay handling -----------------------------------------------------

    default_overlay_options = dict(
        align="center", width=("relative", 80),
        valign="middle", height=("relative", 80),
    )

    def open_overlay(self, widget, options={}, title=""):
        top_widget = RoundedLineBox(widget, title=title)
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
        if self.timeline:
            self.timeline.refresh_status_details()

    def refresh_timeline(self):
        # No point in refreshing the bookmarks timeline
        # and we don't have a good way to refresh a
        # list timeline yet (no reference to list ID kept)
        if (not self.timeline
                or self.timeline.name == 'bookmarks'
                or self.timeline.name.startswith("\N{clipboard}")):
            return

        if self.timeline.name.startswith("#"):
            self.timeline_generator = api.tag_timeline_generator(
                self.app, self.user, self.timeline.name[1:], limit=40)
        elif self.timeline.name.startswith("\N{clipboard}"):
            self.timeline_generator = api.tag_timeline_generator(
                self.app, self.user, self.timeline.name[1:], limit=40)
        else:
            if self.timeline.name.endswith("public"):
                self.timeline_generator = api.public_timeline_generator(
                    self.app, self.user, local=self.timeline.name.startswith("local"), limit=40)
            elif self.timeline.name == "notifications":
                self.timeline_generator = api.notification_timeline_generator(
                    self.app, self.user, limit=40)
            elif self.timeline.name == "conversations":
                self.timeline_generator = api.conversation_timeline_generator(
                    self.app, self.user, limit=40)
            else:
                # default to home timeline
                self.timeline_generator = api.home_timeline_generator(
                    self.app, self.user, limit=40)

        self.async_load_timeline(is_initial=True, timeline_name=self.timeline.name)

    # --- Keys -----------------------------------------------------------------

    def unhandled_input(self, key):
        # TODO: this should not be in unhandled input
        if key in ('x', 'X'):
            if self.exception:
                self.show_exception(self.exception)

        elif key in ('g', 'G'):
            if not self.overlay:
                self.show_goto_menu()

        elif key == '?':
            if not self.overlay:
                self.show_help()

        elif key == ',':
            if not self.overlay:
                self.refresh_timeline()

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
