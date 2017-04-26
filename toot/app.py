# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import curses
import webbrowser

from textwrap import wrap

from toot.utils import format_content


class Color:
    @staticmethod
    def setup_palette():
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    @staticmethod
    def blue():
        return curses.color_pair(1)

    @staticmethod
    def green():
        return curses.color_pair(2)

    @staticmethod
    def yellow():
        return curses.color_pair(3)


class TimelineApp:
    def __init__(self, status_generator):
        self.status_generator = status_generator
        self.statuses = []
        self.selected = None

    def run(self):
        curses.wrapper(self._wrapped_run)

    def _wrapped_run(self, stdscr):
        self.left_width = 60
        self.right_width = curses.COLS - self.left_width

        # Setup windows
        self.top = curses.newwin(2, curses.COLS, 0, 0)
        self.left = curses.newpad(curses.LINES * 2, self.left_width)
        self.right = curses.newwin(curses.LINES - 4, self.right_width, 2, self.left_width)
        self.bottom = curses.newwin(2, curses.COLS, curses.LINES - 2, 0)

        Color.setup_palette()

        # Load some data and redraw
        self.fetch_next()
        self.selected = 0
        self.full_redraw()

        self.loop()

    def loop(self):
        while True:
            key = self.left.getkey()

            if key.lower() == 'q':
                return

            elif key.lower() == 'v':
                status = self.get_selected_status()
                if status:
                    webbrowser.open(status['url'])

            elif key.lower() == 'j' or key == curses.KEY_DOWN:
                self.select_next()

            elif key.lower() == 'k' or key == curses.KEY_UP:
                self.select_previous()

    def select_previous(self):
        """Move to the previous status in the timeline."""
        if self.selected == 0:
            return

        old_index = self.selected
        new_index = self.selected - 1

        self.selected = new_index
        self.redraw_after_selection_change(old_index, new_index)

    def select_next(self):
        """Move to the next status in the timeline."""
        if self.selected + 1 >= len(self.statuses):
            return

        old_index = self.selected
        new_index = self.selected + 1

        self.selected = new_index
        self.redraw_after_selection_change(old_index, new_index)

    def redraw_after_selection_change(self, old_index, new_index):
        old_status = self.statuses[old_index]
        new_status = self.statuses[new_index]

        # Perform a partial redraw
        self.draw_status_row(self.left, old_status, 3 * old_index - 1, False)
        self.draw_status_row(self.left, new_status, 3 * new_index - 1, True)
        self.draw_status_details(self.right, new_status)

    def fetch_next(self):
        try:
            statuses = next(self.status_generator)
        except StopIteration:
            return None

        for status in statuses:
            self.statuses.append(parse_status(status))

        return len(statuses)

    def full_redraw(self):
        """Perform a full redraw of the UI."""
        self.left.clear()
        self.right.clear()
        self.top.clear()
        self.bottom.clear()

        self.left.box()
        self.right.box()

        self.top.addstr(" toot - your Mastodon command line interface\n", Color.yellow())
        self.top.addstr(" https://github.com/ihabunek/toot")

        self.draw_statuses(self.left)
        self.draw_status_details(self.right, self.get_selected_status())
        self.draw_usage(self.bottom)

        self.left.refresh(0, 0, 2, 0, curses.LINES - 4, self.left_width)

        self.right.refresh()
        self.top.refresh()
        self.bottom.refresh()

    def draw_usage(self, window):
        # Show usage on the bottom
        window.addstr("Usage: | ")
        window.addch("j", Color.green())
        window.addstr(" next | ")
        window.addch("k", Color.green())
        window.addstr(" previous | ")
        window.addch("v", Color.green())
        window.addstr(" open in browser | ")
        window.addch("q", Color.green())
        window.addstr(" quit")

        window.refresh()

    def get_selected_status(self):
        if len(self.statuses) > self.selected:
            return self.statuses[self.selected]

    def draw_status_row(self, window, status, offset, highlight=False):
        width = window.getmaxyx()[1]
        color = Color.blue() if highlight else 0

        date, time = status['created_at']
        window.addstr(offset + 2, 2, date, color)
        window.addstr(offset + 3, 2, time, color)

        window.addstr(offset + 2, 15, status['account']['acct'], color)
        window.addstr(offset + 3, 15, status['account']['display_name'], color)

        window.addstr(offset + 4, 1, '─' * (width - 2))

        window.refresh(0, 0, 2, 0, curses.LINES - 4, self.left_width)

    def draw_statuses(self, window):
        for index, status in enumerate(self.statuses):
            offset = 3 * index - 1
            highlight = self.selected == index
            self.draw_status_row(window, status, offset, highlight)

    def draw_status_details(self, window, status):
        window.erase()
        window.box()

        acct = status['account']['acct']
        name = status['account']['display_name']

        window.addstr(1, 2, "@" + acct, Color.green())
        window.addstr(2, 2, name, Color.yellow())

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

        window.addstr(y, 2, status['url'])
        y += 1

        if status['boosted_by']:
            acct = status['boosted_by']['acct']
            window.addstr(y, 2, "Boosted by ")
            window.addstr("@", Color.green())
            window.addstr(acct, Color.green())
            y += 1

        window.refresh()


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
        'url': status['url'],
    }


def parse_account(account):
    return {
        'id': account['id'],
        'acct': account['acct'],
        'display_name': account['display_name'],
    }
