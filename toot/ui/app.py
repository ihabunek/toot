# -*- coding: utf-8 -*-

import webbrowser

from textwrap import wrap

from toot.exceptions import ConsoleError
from toot.ui.utils import draw_horizontal_divider, draw_lines
from toot.utils import format_content, trunc

# Attempt to load curses, which is not available on windows
try:
    import curses
except ImportError as e:
    raise ConsoleError("Curses is not available on this platform")


class Color:
    @classmethod
    def setup_palette(class_):
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLUE)

        class_.WHITE = curses.color_pair(1)
        class_.BLUE = curses.color_pair(2)
        class_.GREEN = curses.color_pair(3)
        class_.YELLOW = curses.color_pair(4)
        class_.RED = curses.color_pair(5)
        class_.WHITE_ON_BLUE = curses.color_pair(6)


class HeaderWindow:
    def __init__(self, height, width, y, x):
        self.window = curses.newwin(height, width, y, x)
        self.height = height
        self.width = width

    def draw(self):
        self.window.erase()
        self.window.addstr(0, 1, "toot - your Mastodon command line interface", Color.YELLOW)
        self.window.addstr(1, 1, "https://github.com/ihabunek/toot")
        self.window.refresh()


class FooterWindow:
    def __init__(self, height, width, y, x):
        self.window = curses.newwin(height, width, y, x)
        self.height = height
        self.width = width

    def draw_status(self, selected, count):
        text = "Showing toot {} of {}".format(selected + 1, count)
        text = trunc(text, self.width - 1).ljust(self.width - 1)
        self.window.addstr(0, 0, text, Color.WHITE_ON_BLUE | curses.A_BOLD)
        self.window.refresh()

    def draw_message(self, text, color):
        text = trunc(text, self.width - 1).ljust(self.width - 1)
        self.window.addstr(1, 0, text, color)
        self.window.refresh()

    def clear_message(self):
        self.window.addstr(1, 0, "".ljust(self.width - 1))
        self.window.refresh()


class StatusListWindow:
    """Window which shows the scrollable list of statuses (left side)."""
    def __init__(self, height, width, top, left):
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

        date, time = status['created_at']
        self.pad.addstr(offset + 1, 1, " " + date.ljust(14), color)
        self.pad.addstr(offset + 2, 1, " " + time.ljust(14), color)

        trunc_width = width - 15
        acct = trunc("@" + status['account']['acct'], trunc_width).ljust(trunc_width)
        display_name = trunc(status['account']['display_name'], trunc_width).ljust(trunc_width)

        if status['account']['display_name']:
            self.pad.addstr(offset + 1, 14, display_name, color)
            self.pad.addstr(offset + 2, 14, acct, color)
        else:
            self.pad.addstr(offset + 1, 14, acct, color)

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
    def __init__(self, height, width, y, x):
        self.window = curses.newwin(height, width, y, x)
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

        for line in status['lines']:
            wrapped_lines = wrap(line, text_width) if line else ['']
            for wrapped_line in wrapped_lines:
                yield wrapped_line.ljust(text_width)

        if status['media_attachments']:
            yield
            yield "Media:"
            for attachment in status['media_attachments']:
                url = attachment['text_url'] or attachment['url']
                for line in wrap(url, text_width):
                    yield line

    def footer_lines(self, status):
        text_width = self.width - 4

        if status['url'] is not None:
            for line in wrap(status['url'], text_width):
                yield line

        if status['boosted_by']:
            acct = status['boosted_by']['acct']
            yield "Boosted by @{}".format(acct), Color.BLUE

    def draw(self, status):
        self.window.erase()
        self.window.box()

        if not status:
            return

        content = self.content_lines(status)
        footer = self.footer_lines(status)

        y = draw_lines(self.window, content, 2, 1, Color.WHITE)
        draw_horizontal_divider(self.window, y)
        draw_lines(self.window, footer, 2, y + 1, Color.WHITE)

        self.window.refresh()


class TimelineApp:
    def __init__(self, status_generator):
        self.status_generator = status_generator
        self.statuses = []
        self.stdscr = None

    def run(self):
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

        left_width = max(min(screen_width // 3, 60), 30)
        right_width = screen_width - left_width

        self.header = HeaderWindow(2, screen_width, 0, 0)
        self.footer = FooterWindow(2, screen_width, screen_height - 2, 0)
        self.left = StatusListWindow(screen_height - 4, left_width, 2, 0)
        self.right = StatusDetailWindow(screen_height - 4, right_width, 2, left_width)

    def loop(self):
        while True:
            key = self.left.pad.getkey()

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

    def full_redraw(self):
        """Perform a full redraw of the UI."""
        self.header.draw()
        self.draw_footer_status()

        self.left.draw_statuses(self.statuses, self.selected)
        self.right.draw(self.get_selected_status())
        self.header.draw()

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
