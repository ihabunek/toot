# -*- coding: utf-8 -*-

import webbrowser

from textwrap import wrap

from toot.exceptions import ConsoleError
from toot.utils import format_content, trunc

# Attempt to load curses, which is not available on windows
try:
    import curses
except ImportError as e:
    raise ConsoleError("Curses is not available on this platform")


class Color:
    @classmethod
    def setup_palette(class_):
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLUE)

        class_.BLUE = curses.color_pair(1)
        class_.GREEN = curses.color_pair(2)
        class_.YELLOW = curses.color_pair(3)
        class_.RED = curses.color_pair(4)
        class_.WHITE_ON_BLUE = curses.color_pair(5)


class TimelineApp:
    def __init__(self, status_generator):
        self.status_generator = status_generator
        self.statuses = []
        self.selected = None
        self.stdscr = None
        self.scroll_pos = 0

    def run(self):
        curses.wrapper(self._wrapped_run)

    def _wrapped_run(self, stdscr):
        self.stdscr = stdscr

        self.setup_windows()
        Color.setup_palette()

        # Load some data and redraw
        self.fetch_next()
        self.selected = 0
        self.full_redraw()

        self.loop()

    def setup_windows(self):
        screen_height, screen_width = self.stdscr.getmaxyx()

        if screen_width < 60:
            raise ConsoleError("Terminal screen is too narrow, toot curses requires at least 60 columns to display properly.")

        self.left_width = max(min(screen_width // 3, 60), 30)
        self.right_width = screen_width - self.left_width

        self.top = curses.newwin(2, screen_width, 0, 0)
        self.left = curses.newpad(screen_height - 4, self.left_width)
        self.right = curses.newwin(screen_height - 4, self.right_width, 2, self.left_width)
        self.bottom = curses.newwin(2, screen_width, screen_height - 2, 0)

    def loop(self):
        while True:
            key = self.left.getkey()

            if key.lower() == 'q':
                return

            elif key.lower() == 'v':
                status = self.get_selected_status()
                if status:
                    webbrowser.open(status['url'])

            elif key.lower() == 'j' or key == 'B':
                self.select_next()

            elif key.lower() == 'k' or key == 'A':
                self.select_previous()

            elif key == 'KEY_RESIZE':
                self.setup_windows()
                self.full_redraw()

    def scroll_to(self, index):
        self.scroll_pos = index
        height, width = self.stdscr.getmaxyx()

        self.left.refresh(3 * index, 0, 2, 0, height - 4, self.left_width)

    def scroll_up(self):
        if self.scroll_pos > 0:
            self.scroll_to(self.scroll_pos - 1)

    def scroll_down(self):
        self.scroll_to(self.scroll_pos + 1)

    def scroll_refresh(self):
        self.scroll_to(self.scroll_pos)

    def select_previous(self):
        """Move to the previous status in the timeline."""
        self.clear_bottom_message()

        if self.selected == 0:
            self.draw_bottom_message("Cannot move beyond first toot.", Color.GREEN)
            return

        old_index = self.selected
        new_index = self.selected - 1

        self.selected = new_index
        self.redraw_after_selection_change(old_index, new_index)

        # Scroll if required
        if new_index < self.scroll_pos:
            self.scroll_up()
        else:
            self.scroll_refresh()

    def select_next(self):
        """Move to the next status in the timeline."""
        self.clear_bottom_message()

        # Load more statuses if no more are available
        if self.selected + 1 >= len(self.statuses):
            self.fetch_next()
            self.draw_statuses(self.left, self.selected + 1)
            self.draw_bottom_status()

        old_index = self.selected
        new_index = self.selected + 1

        self.selected = new_index
        self.redraw_after_selection_change(old_index, new_index)

        # Scroll if required
        if new_index >= self.scroll_pos + self.get_page_size():
            self.scroll_down()
        else:
            self.scroll_refresh()

    def get_page_size(self):
        """Calculate how many statuses fit on one page (3 lines per status)"""
        height = self.right.getmaxyx()[0] - 2  # window height - borders
        return height // 3

    def redraw_after_selection_change(self, old_index, new_index):
        old_status = self.statuses[old_index]
        new_status = self.statuses[new_index]

        # Perform a partial redraw
        self.draw_status_row(self.left, old_status, old_index, False)
        self.draw_status_row(self.left, new_status, new_index, True)
        self.draw_status_details(self.right, new_status)
        self.draw_bottom_status()

    def fetch_next(self):
        try:
            self.draw_bottom_message("Loading toots...", Color.BLUE)
            statuses = next(self.status_generator)
        except StopIteration:
            return None

        for status in statuses:
            self.statuses.append(parse_status(status))

        self.draw_bottom_message("Loaded {} toots".format(len(statuses)), Color.GREEN)

        return len(statuses)

    def full_redraw(self):
        """Perform a full redraw of the UI."""
        self.left.clear()
        self.right.clear()
        self.top.clear()
        self.bottom.clear()

        self.left.box()
        self.right.box()

        self.top.addstr(" toot - your Mastodon command line interface\n", Color.YELLOW)
        self.top.addstr(" https://github.com/ihabunek/toot")

        self.draw_statuses(self.left)
        self.draw_status_details(self.right, self.get_selected_status())
        self.draw_usage(self.bottom)
        self.draw_bottom_status()

        self.scroll_refresh()

        self.right.refresh()
        self.top.refresh()
        self.bottom.refresh()

    def draw_usage(self, window):
        # Show usage on the bottom
        window.addstr("Usage: | ")
        window.addch("j", Color.GREEN)
        window.addstr(" next | ")
        window.addch("k", Color.GREEN)
        window.addstr(" previous | ")
        window.addch("v", Color.GREEN)
        window.addstr(" open in browser | ")
        window.addch("q", Color.GREEN)
        window.addstr(" quit")

        window.refresh()

    def get_selected_status(self):
        if len(self.statuses) > self.selected:
            return self.statuses[self.selected]

    def draw_status_row(self, window, status, index, highlight=False):
        offset = 3 * index

        height, width = window.getmaxyx()
        color = Color.BLUE if highlight else 0

        date, time = status['created_at']
        window.addstr(offset + 1, 2, date, color)
        window.addstr(offset + 2, 2, time, color)

        trunc_width = width - 16
        acct = trunc(status['account']['acct'], trunc_width).ljust(trunc_width)
        display_name = trunc(status['account']['display_name'], trunc_width).ljust(trunc_width)

        window.addstr(offset + 1, 14, acct, color)
        window.addstr(offset + 2, 14, display_name, color)
        window.addstr(offset + 3, 1, '─' * (width - 2))

        screen_height, screen_width = self.stdscr.getmaxyx()
        window.refresh(0, 0, 2, 0, screen_height - 4, self.left_width)

    def draw_statuses(self, window, starting=0):
        # Resize window to accomodate statuses if required
        height, width = window.getmaxyx()
        new_height = len(self.statuses) * 3 + 1
        if new_height > height:
            window.resize(new_height, width)
            window.box()

        for index, status in enumerate(self.statuses):
            if index >= starting:
                highlight = self.selected == index
                self.draw_status_row(window, status, index, highlight)

    def draw_status_details(self, window, status):
        window.erase()
        window.box()

        acct = status['account']['acct']
        name = status['account']['display_name']

        window.addstr(1, 2, "@" + acct, Color.GREEN)
        window.addstr(2, 2, name, Color.YELLOW)

        y = 4
        text_width = self.right_width - 4

        for line in status['lines']:
            wrapped_lines = wrap(line, text_width) if line else ['']
            for wrapped_line in wrapped_lines:
                window.addstr(y, 2, wrapped_line.ljust(text_width))
                y = y + 1

        if status['media_attachments']:
            y += 1
            for attachment in status['media_attachments']:
                url = attachment['text_url'] or attachment['url']
                for line in wrap(url, text_width):
                    window.addstr(y, 2, line)
                    y += 1

        window.addstr(y, 1, '-' * (text_width + 2))
        y += 1

        if status['url'] is not None:
            window.addstr(y, 2, status['url'])
            y += 1

        if status['boosted_by']:
            acct = status['boosted_by']['acct']
            window.addstr(y, 2, "Boosted by ")
            window.addstr("@", Color.GREEN)
            window.addstr(acct, Color.GREEN)
            y += 1

        window.refresh()

    def clear_bottom_message(self):
        _, width = self.bottom.getmaxyx()
        self.bottom.addstr(1, 0, " " * (width - 1))
        self.bottom.refresh()

    def draw_bottom_message(self, text, color=0):
        _, width = self.bottom.getmaxyx()
        text = trunc(text, width - 1).ljust(width - 1)
        self.bottom.addstr(1, 0, text, color)
        self.bottom.refresh()

    def draw_bottom_status(self):
        _, width = self.bottom.getmaxyx()
        text = "Showing toot {} of {}".format(self.selected + 1, len(self.statuses))
        text = trunc(text, width - 1).ljust(width - 1)
        self.bottom.addstr(0, 0, text, Color.WHITE_ON_BLUE | curses.A_BOLD)
        self.bottom.refresh()


def parse_status(status):
    _status = status.get('reblog') or status
    account = parse_account(_status['account'])
    lines = list(format_content(_status['content']))

    created_at = status['created_at'][:19].split('T')
    boosted_by = parse_account(status['account']) if status['reblog'] else None

    return {
        'account': account,
        'boosted_by': boosted_by,
        'created_at': created_at,
        'lines': lines,
        'media_attachments': _status['media_attachments'],
        'url': _status['url'],
    }


def parse_account(account):
    return {
        'id': account['id'],
        'acct': account['acct'],
        'display_name': account['display_name'],
    }
