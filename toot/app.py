# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import curses
import re
import webbrowser

from bs4 import BeautifulSoup
from textwrap import wrap


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
            statuses = self.status_generator.__next__()
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

        window.addstr(offset + 2, 15, status['author']['acct'], color)
        window.addstr(offset + 3, 15, status['author']['display_name'], color)

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

        acct = status['author']['acct']
        name = status['author']['display_name']

        window.addstr(1, 2, "@" + acct, Color.green())
        window.addstr(2, 2, name, Color.yellow())

        text_width = self.right_width - 4

        y = 4
        for line in status['lines']:
            for wrapped in wrap(line, text_width):
                window.addstr(y, 2, wrapped.ljust(text_width))
                y += 1
            y += 1

        window.addstr(y, 2, '─' * text_width)
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
    content = status['reblog']['content'] if status['reblog'] else status['content']
    account = parse_account(status['reblog']['account'] if status['reblog'] else status['account'])
    boosted_by = parse_account(status['account']) if status['reblog'] else None

    lines = parse_html(content)

    created_at = status['created_at'][:19].split('T')

    return {
        'author': account,
        'boosted_by': boosted_by,
        'lines': lines,
        'url': status['url'],
        'created_at': created_at,
    }


def parse_account(account):
    return {
        'id': account['id'],
        'acct': account['acct'],
        'display_name': account['display_name'],
    }


def parse_html(html):
    """Attempt to convert html to plain text while keeping line breaks"""
    return [
        BeautifulSoup(l, "html.parser").get_text().replace('&apos;', "'")
        for l in re.split("</?p[^>]*>", html)
        if l
    ]
