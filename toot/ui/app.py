# -*- coding: utf-8 -*-
import os
import webbrowser

from toot import __version__, api

from toot.exceptions import ConsoleError
from toot.ui.parsers import parse_status
from toot.ui.utils import draw_horizontal_divider, draw_lines, size_as_drawn
from toot.wcstring import fit_text

# Attempt to load curses, which is not available on windows
try:
    import curses
    import curses.panel
    import curses.textpad
except ImportError:
    raise ConsoleError("Curses is not available on this platform")


class Color:
    @classmethod
    def setup_palette(class_):
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(9, curses.COLOR_WHITE, curses.COLOR_RED)

        class_.WHITE = curses.color_pair(1)
        class_.BLUE = curses.color_pair(2)
        class_.GREEN = curses.color_pair(3)
        class_.YELLOW = curses.color_pair(4)
        class_.RED = curses.color_pair(5)
        class_.CYAN = curses.color_pair(6)
        class_.MAGENTA = curses.color_pair(7)
        class_.WHITE_ON_BLUE = curses.color_pair(8)
        class_.WHITE_ON_RED = curses.color_pair(9)

        class_.HASHTAG = class_.BLUE | curses.A_BOLD


class HeaderWindow:
    def __init__(self, stdscr, height, width, y, x):
        self.window = stdscr.subwin(height, width, y, x)
        self.window.bkgdset(' ', Color.WHITE_ON_BLUE)
        self.height = height
        self.width = width

    def draw(self, user):
        username = "{}@{}".format(user.username, user.instance)

        self.window.erase()
        self.window.addstr("  toot", curses.A_BOLD)
        self.window.addstr(" | ")
        self.window.addstr(username)
        self.window.addstr(" | ")
        self.window.refresh()


class FooterWindow:
    def __init__(self, stdscr, height, width, y, x):
        self.window = stdscr.subwin(height, width, y, x)
        self.height = height
        self.width = width

    def draw_status(self, selected, count):
        text = "Showing toot {} of {}".format(selected + 1, count)
        text = fit_text(text, self.width)
        self.window.addstr(0, 0, text, Color.WHITE_ON_BLUE | curses.A_BOLD)
        self.window.refresh()

    def draw_message(self, text, color):
        text = fit_text(text, self.width - 1)
        self.window.addstr(1, 0, text, color)
        self.window.refresh()

    def clear_message(self):
        self.window.addstr(1, 0, "".ljust(self.width - 1))
        self.window.refresh()


class StatusListWindow:
    """Window which shows the scrollable list of statuses (left side)."""
    def __init__(self, stdscr, height, width, top, left):
        # Dimensions and position of region in stdscr which will contain the pad
        self.region_height = height
        self.region_width = width
        self.region_top = top
        self.region_left = left

        # How many statuses fit on one page (excluding border, at 3 lines per status)
        self.page_size = (height - 2) // 3

        # Initially, size the pad to the dimensions of the region, will be
        # increased later to accomodate statuses
        self.pad = curses.newpad(10, width)
        self.pad.box()

        # Make curses interpret escape sequences for getch (why is this off by default?)
        self.pad.keypad(True)

        self.scroll_pos = 0

    def draw_statuses(self, statuses, selected, starting=0):
        # Resize window to accomodate statuses if required
        height, width = self.pad.getmaxyx()

        new_height = len(statuses) * 3 + 1
        if new_height > height:
            self.pad.resize(new_height, width)
            self.pad.box()

        last_idx = len(statuses) - 1

        for index, status in enumerate(statuses):
            if index >= starting:
                highlight = selected == index
                draw_divider = index < last_idx
                self.draw_status_row(status, index, highlight, draw_divider)

    def draw_status_row(self, status, index, highlight=False, draw_divider=True):
        offset = 3 * index

        height, width = self.pad.getmaxyx()
        color = Color.GREEN if highlight else Color.WHITE

        trunc_width = width - 15
        acct = fit_text("@" + status['account']['acct'], trunc_width)
        display_name = fit_text(status['account']['display_name'], trunc_width)

        if status['account']['display_name']:
            self.pad.addstr(offset + 1, 14, display_name, color)
            self.pad.addstr(offset + 2, 14, acct, color)
        else:
            self.pad.addstr(offset + 1, 14, acct, color)
        if status['in_reply_to_id'] is not None:
            self.pad.addstr(offset + 1, width - 3, '⤶', Color.CYAN)

        date, time = status['created_at']
        self.pad.addstr(offset + 1, 1, " " + date.ljust(12), color)
        self.pad.addstr(offset + 2, 1, " " + time.ljust(12), color)

        if status['favourited']:
            self.pad.addstr(offset + 2, width - 3, '⭐', Color.YELLOW)

        if draw_divider:
            draw_horizontal_divider(self.pad, offset + 3)

        self.refresh()

    def refresh(self):
        self.pad.refresh(
            self.scroll_pos * 3,  # top
            0,                    # left
            self.region_top,
            self.region_left,
            self.region_height + 1,  # +1 required to refresh full height, not sure why
            self.region_width,
        )

    def scroll_to(self, index):
        self.scroll_pos = index
        self.refresh()

    def scroll_up(self):
        if self.scroll_pos > 0:
            self.scroll_to(self.scroll_pos - 1)

    def scroll_down(self):
        self.scroll_to(self.scroll_pos + 1)

    def scroll_if_required(self, new_index):
        if new_index < self.scroll_pos:
            self.scroll_up()
        elif new_index >= self.scroll_pos + self.page_size:
            self.scroll_down()
        else:
            self.refresh()


class StatusDetailWindow:
    """Window which shows details of a status (right side)"""
    def __init__(self, stdscr, height, width, y, x):
        self.window = stdscr.subwin(height, width, y, x)
        self.height = height
        self.width = width

    def content_lines(self, status):
        acct = status['account']['acct']
        name = status['account']['display_name']

        if name:
            yield name, Color.YELLOW
        yield "@" + acct, Color.GREEN
        yield

        text_width = self.width - 4

        if status['sensitive']:
            for line in status['spoiler_text']:
                yield line
            yield

        if status['sensitive'] and not status['show_sensitive']:
            yield "Marked as sensitive, press s to view".ljust(text_width), Color.WHITE_ON_RED
            return

        for line in status['content']:
            yield line

        if status['media_attachments']:
            yield
            yield "Media:"
            for attachment in status['media_attachments']:
                yield attachment['text_url'] or attachment['url']

    def footer_lines(self, status):
        if status['url'] is not None:
            yield status['url']

        if status['boosted_by']:
            acct = status['boosted_by']['acct']
            yield "Boosted by @{}".format(acct), Color.GREEN

        if status['reblogged']:
            yield "↷ Boosted", Color.CYAN

        yield (
            "{replies_count} replies, "
            "{reblogs_count} reblogs, "
            "{favourites_count} favourites"
        ).format(**status), Color.CYAN

    def draw(self, status):
        self.window.erase()
        self.window.box()

        if not status:
            return

        content = self.content_lines(status)
        footer = self.footer_lines(status)

        y = draw_lines(self.window, content, 1, 2, Color.WHITE)
        draw_horizontal_divider(self.window, y)
        draw_lines(self.window, footer, y + 1, 2, Color.WHITE)

        self.window.refresh()


class Modal:
    def __init__(self, stdscr, resize_callback=None):
        self.stdscr = stdscr
        self.resize_callback = resize_callback

        self.setup_windows()
        self.full_redraw()
        self.panel = curses.panel.new_panel(self.window)
        self.hide()

    def get_content(self):
        raise NotImplementedError()

    def get_size_pos(self, stdscr):
        screen_height, screen_width = stdscr.getmaxyx()

        content = self.get_content()
        height = len(content) + 2
        width = max(len(l) for l in content) + 4

        y = (screen_height - height) // 2
        x = (screen_width - width) // 2

        return height, width, y, x

    def setup_windows(self):
        height, width, y, x = self.get_size_pos(self.stdscr)
        self.window = curses.newwin(height, width, y, x)

    def full_redraw(self):
        self.setup_windows()
        self.window.box()
        draw_lines(self.window, self.get_content(), 1, 2, Color.WHITE)

    def show(self):
        self.panel.top()
        self.panel.show()
        self.window.refresh()
        curses.panel.update_panels()

    def hide(self):
        self.panel.hide()
        curses.panel.update_panels()

    def loop(self):
        self.show()

        while True:
            ch = self.window.getch()
            key = chr(ch).lower() if curses.ascii.isprint(ch) else None

            if key == 'q':
                break
            elif ch == curses.KEY_RESIZE:
                if self.resize_callback:
                    self.resize_callback()
                self.full_redraw()

        self.hide()


class HelpModal(Modal):
    def get_content(self):
        return [
            ("toot v{}".format(__version__), Color.GREEN | curses.A_BOLD),
            "",
            "Key bindings:",
            "",
            "  h      - show help",
            "  j or ↓ - move down",
            "  k or ↑ - move up",
            "  v      - view current toot in browser",
            "  b      - toggle boost status",
            "  f      - toggle favourite status",
            "  c      - post a new status",
            "  r      - reply to status",
            "  q      - quit application",
            "  s      - show sensitive content"
            "",
            "Press q to exit help.",
            "",
            ("https://github.com/ihabunek/toot", Color.YELLOW),
        ]


class EntryModal(Modal):
    def __init__(self, stdscr, title, footer=None, size=(None, None), default=None, resize_callback=None):
        self.stdscr = stdscr
        self.resize_callback = resize_callback
        self.content = [] if default is None else default.split()
        self.cursor_pos = 0
        self.pad_y, self.pad_x = 2, 2

        self.title = title
        self.footer = footer
        self.size = size
        if self.footer:
            self.pad_y += 1

        self.setup_windows()
        self.full_redraw()
        self.panel = curses.panel.new_panel(self.window)
        self.hide()

    def get_size_pos(self, stdscr):
        screen_height, screen_width = stdscr.getmaxyx()
        if self.size[0]:
            height = self.size[0] + (self.pad_y * 2) + 1
        else:
            height = int(screen_height / 1.33)
        if self.size[1]:
            width = self.size[1] + (self.pad_x * 2) + 1
        else:
            width = int(screen_width / 1.25)

        y = (screen_height - height) // 2
        x = (screen_width - width) // 2

        return height, width, y, x

    def setup_windows(self):
        height, width, y, x = self.get_size_pos(self.stdscr)

        self.window = curses.newwin(height, width, y, x)
        self.text_window = self.window.derwin(height - (self.pad_y * 2), width - (self.pad_x * 2), self.pad_y, self.pad_x)
        self.text_window.keypad(True)

    def full_redraw(self):
        self.window.erase()
        self.window.box()

        draw_lines(self.window, ["{}  (^D to confirm):".format(self.title)], 1, 2, Color.WHITE)
        if self.footer:
            window_height, window_width = self.window.getmaxyx()
            draw_lines(self.window, [self.footer], window_height - self.pad_y + 1, 2, Color.WHITE)

        self.window.refresh()
        self.refresh_text()

    def refresh_text(self):
        text = self.get_content()
        lines = text.split('\n')
        draw_lines(self.text_window, lines, 0, 0, Color.WHITE)

        text_window_height, text_window_width = self.text_window.getmaxyx()
        text_on_screen = (''.join(self.content)[:self.cursor_pos] + '_').split('\n')
        y, x = size_as_drawn(text_on_screen, text_window_width)
        self.text_window.move(y, x)

    def show(self):
        super().show()
        self.refresh_text()

    def clear(self):
        self.content = []
        self.cursor_pos = 0

    def on_resize(self):
        if self.resize_callback:
            self.resize_callback()
        self.setup_windows()
        self.full_redraw()

    def do_command(self, ch):
        if curses.ascii.isprint(ch) or ch == curses.ascii.LF:
            text_window_height, text_window_width = self.text_window.getmaxyx()
            y, x = size_as_drawn((self.get_content() + chr(ch)).split('\n'), text_window_width)
            if y < text_window_height - 1 and x < text_window_width:
                self.content.insert(self.cursor_pos, chr(ch))
                self.cursor_pos += 1
            else:
                curses.beep()

        elif ch == curses.KEY_BACKSPACE:
            if self.cursor_pos > 0:
                del self.content[self.cursor_pos - 1]
                self.cursor_pos -= 1
            else:
                curses.beep()

        elif ch == curses.KEY_DC:
            if self.cursor_pos >= 0 and self.cursor_pos < len(self.content):
                del self.content[self.cursor_pos]
            else:
                curses.beep()

        elif ch == curses.KEY_LEFT:
            if self.cursor_pos > 0:
                self.cursor_pos -= 1
            else:
                curses.beep()

        elif ch == curses.KEY_RIGHT:
            if self.cursor_pos + 1 <= len(self.content):
                self.cursor_pos += 1
            else:
                curses.beep()

        elif ch in (curses.ascii.EOT, curses.ascii.RS):  # ^D or (for some terminals) Ctrl+Enter
            return False, False

        elif ch == curses.ascii.ESC:
            self.clear()
            return False, True

        elif ch == curses.KEY_RESIZE:
            self.on_resize()
            return True, False

        self.refresh_text()
        return True, False

    def get_content(self):
        return ''.join(self.content)

    def loop(self):
        self.show()
        while True:
            ch = self.text_window.getch()
            if not ch:
                continue
            should_continue, abort_flag = self.do_command(ch)
            if not should_continue:
                break
        self.hide()
        if abort_flag:
            return None
        else:
            return self.get_content()


class ComposeModal(EntryModal):
    def __init__(self, stdscr, default_cw=None, **kwargs):
        super().__init__(stdscr, title="Compose a toot", footer="^D to submit, ESC to quit, ^W to mark sensitive (cw)", **kwargs)
        self.cw = default_cw
        self.cwmodal = EntryModal(stdscr, title="Content warning", size=(1, 60), default=self.cw, resize_callback=self.on_resize)

    def do_command(self, ch):
        if ch == curses.ascii.ctrl(ord('w')):
            self.cwmodal.on_resize()
            self.cw = self.cwmodal.loop() or None
            self.full_redraw()
            return True, False
        else:
            return super().do_command(ch)

    def loop(self):
        content = super().loop()
        return content, self.cw


class TimelineApp:
    def __init__(self, app, user, status_generator):
        self.app = app
        self.user = user
        self.status_generator = status_generator
        self.statuses = []
        self.stdscr = None

    def run(self):
        os.environ.setdefault('ESCDELAY', '25')
        curses.wrapper(self._wrapped_run)

    def _wrapped_run(self, stdscr):
        self.stdscr = stdscr

        Color.setup_palette()
        self.setup_windows()

        # Load some data and redraw
        self.fetch_next()
        self.selected = 0
        self.full_redraw()

        self.loop()

    def setup_windows(self):
        screen_height, screen_width = self.stdscr.getmaxyx()

        if screen_width < 60:
            raise ConsoleError("Terminal screen is too narrow, toot curses requires at least 60 columns to display properly.")

        header_height = 1
        footer_height = 2
        footer_top = screen_height - footer_height

        left_width = max(min(screen_width // 3, 60), 30)
        main_height = screen_height - header_height - footer_height
        main_width = screen_width - left_width

        self.header = HeaderWindow(self.stdscr, header_height, screen_width, 0, 0)
        self.footer = FooterWindow(self.stdscr, footer_height, screen_width, footer_top, 0)
        self.left = StatusListWindow(self.stdscr, main_height, left_width, header_height, 0)
        self.right = StatusDetailWindow(self.stdscr, main_height, main_width, header_height, left_width)

        self.help_modal = HelpModal(self.stdscr, resize_callback=self.on_resize)

    def loop(self):
        while True:
            ch = self.left.pad.getch()
            key = chr(ch).lower() if curses.ascii.isprint(ch) else None

            if key == 'q':
                return

            elif key == 'h':
                self.help_modal.loop()
                self.full_redraw()

            elif key == 'v':
                status = self.get_selected_status()
                if status:
                    webbrowser.open(status['url'])

            elif key == 'j' or ch == curses.KEY_DOWN:
                self.select_next()

            elif key == 'k' or ch == curses.KEY_UP:
                self.select_previous()

            elif key == 's':
                self.show_sensitive()

            elif key == 'b':
                self.toggle_reblog()

            elif key == 'f':
                self.toggle_favourite()

            elif key == 'c':
                self.compose()

            elif key == 'r':
                self.reply()

            elif ch == curses.KEY_RESIZE:
                self.on_resize()

    def show_sensitive(self):
        status = self.get_selected_status()
        if status['sensitive'] and not status['show_sensitive']:
            status['show_sensitive'] = True
            self.right.draw(status)

    def compose(self):
        """Compose and submit a new status"""
        app, user = self.app, self.user
        if not app or not user:
            self.footer.draw_message("You must be logged in to post", Color.RED)
            return

        compose_modal = ComposeModal(self.stdscr, resize_callback=self.on_resize)
        content, cw = compose_modal.loop()
        self.full_redraw()
        if content is None:
            return
        elif len(content) == 0:
            self.footer.draw_message("Status must contain content", Color.RED)
            return

        self.footer.draw_message("Submitting status...", Color.YELLOW)
        response = api.post_status(app, user, content, spoiler_text=cw, sensitive=cw is not None)
        status = parse_status(response)
        self.statuses.insert(0, status)
        self.selected += 1
        self.left.draw_statuses(self.statuses, self.selected)
        self.footer.draw_message("✓ Status posted", Color.GREEN)

    def reply(self):
        """Reply to the selected status"""
        status = self.get_selected_status()
        app, user = self.app, self.user
        if not app or not user:
            self.footer.draw_message("You must be logged in to reply", Color.RED)
            return

        compose_modal = ComposeModal(self.stdscr, default_cw='\n'.join(status['spoiler_text']) or None, resize_callback=self.on_resize)
        content, cw = compose_modal.loop()
        self.full_redraw()
        if content is None:
            return
        elif len(content) == 0:
            self.footer.draw_message("Status must contain content", Color.RED)
            return

        self.footer.draw_message("Submitting reply...", Color.YELLOW)
        response = api.post_status(app, user, content, spoiler_text=cw, sensitive=cw is not None, in_reply_to_id=status['id'])
        status = parse_status(response)
        self.statuses.insert(0, status)
        self.selected += 1
        self.left.draw_statuses(self.statuses, self.selected)
        self.footer.draw_message("✓ Reply posted", Color.GREEN)

    def toggle_reblog(self):
        """Reblog or unreblog selected status."""
        status = self.get_selected_status()
        assert status
        app, user = self.app, self.user
        if not app or not user:
            self.footer.draw_message("You must be logged in to reblog", Color.RED)
            return
        status_id = status['id']
        if status['reblogged']:
            status['reblogged'] = False
            self.footer.draw_message("Unboosting status...", Color.YELLOW)
            api.unreblog(app, user, status_id)
            self.footer.draw_message("✓ Status unboosted", Color.GREEN)
        else:
            status['reblogged'] = True
            self.footer.draw_message("Boosting status...", Color.YELLOW)
            api.reblog(app, user, status_id)
            self.footer.draw_message("✓ Status boosted", Color.GREEN)

        self.right.draw(status)

    def toggle_favourite(self):
        """Favourite or unfavourite selected status."""
        status = self.get_selected_status()
        assert status
        app, user = self.app, self.user
        if not app or not user:
            self.footer.draw_message("You must be logged in to favourite", Color.RED)
            return
        status_id = status['id']
        if status['favourited']:
            self.footer.draw_message("Undoing favourite status...", Color.YELLOW)
            api.unfavourite(app, user, status_id)
            self.footer.draw_message("✓ Status unfavourited", Color.GREEN)
        else:
            self.footer.draw_message("Favourite status...", Color.YELLOW)
            api.favourite(app, user, status_id)
            self.footer.draw_message("✓ Status favourited", Color.GREEN)
        status['favourited'] = not status['favourited']

        self.right.draw(status)

    def select_previous(self):
        """Move to the previous status in the timeline."""
        self.footer.clear_message()

        if self.selected == 0:
            self.footer.draw_message("Cannot move beyond first toot.", Color.GREEN)
            return

        old_index = self.selected
        new_index = self.selected - 1

        self.selected = new_index
        self.redraw_after_selection_change(old_index, new_index)

    def select_next(self):
        """Move to the next status in the timeline."""
        self.footer.clear_message()

        old_index = self.selected
        new_index = self.selected + 1

        # Load more statuses if no more are available
        if self.selected + 1 >= len(self.statuses):
            self.fetch_next()
            self.left.draw_statuses(self.statuses, self.selected, new_index - 1)
            self.draw_footer_status()

        self.selected = new_index
        self.redraw_after_selection_change(old_index, new_index)

    def fetch_next(self):
        try:
            self.footer.draw_message("Loading toots...", Color.BLUE)
            statuses = next(self.status_generator)
        except StopIteration:
            return None

        for status in statuses:
            self.statuses.append(parse_status(status))

        self.footer.draw_message("Loaded {} toots".format(len(statuses)), Color.GREEN)

        return len(statuses)

    def on_resize(self):
        self.setup_windows()
        self.full_redraw()

    def full_redraw(self):
        """Perform a full redraw of the UI."""
        self.left.draw_statuses(self.statuses, self.selected)
        self.right.draw(self.get_selected_status())

        self.header.draw(self.user)
        self.draw_footer_status()


    def redraw_after_selection_change(self, old_index, new_index):
        old_status = self.statuses[old_index]
        new_status = self.statuses[new_index]

        # Perform a partial redraw
        self.left.draw_status_row(old_status, old_index, highlight=False, draw_divider=False)
        self.left.draw_status_row(new_status, new_index, highlight=True, draw_divider=False)
        self.left.scroll_if_required(new_index)

        self.right.draw(new_status)
        self.draw_footer_status()

    def get_selected_status(self):
        if len(self.statuses) > self.selected:
            return self.statuses[self.selected]

    def draw_footer_status(self):
        self.footer.draw_status(self.selected, len(self.statuses))
