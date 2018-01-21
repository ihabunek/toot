import re

from textwrap import wrap


def draw_horizontal_divider(window, y):
    height, width = window.getmaxyx()

    # Don't draw out of bounds
    if y < height - 1:
        line = '├' + '─' * (width - 2) + '┤'
        window.addstr(y, 0, line)


def enumerate_lines(lines, text_width, default_color):
    def parse_line(line):
        if isinstance(line, tuple) and len(line) == 2:
            return line[0], line[1]
        elif isinstance(line, str):
            return line, default_color
        elif line is None:
            return "", default_color

        raise ValueError("Wrong yield in generator")

    def wrap_lines(lines):
        for line in lines:
            line, color = parse_line(line)
            if line:
                for wrapped in wrap(line, text_width):
                    yield wrapped, color
            else:
                yield "", color

    return enumerate(wrap_lines(lines))


HASHTAG_PATTERN = re.compile(r'(?<!\w)(#\w+)\b')


def highlight_hashtags(window, y, padding, line):
    from toot.ui.app import Color

    for match in re.finditer(HASHTAG_PATTERN, line):
        start, end = match.span()
        window.chgat(y, start + padding, end - start, Color.HASHTAG)


def draw_lines(window, lines, start_y, padding, default_color):
    height, width = window.getmaxyx()
    text_width = width - 2 * padding

    for dy, (line, color) in enumerate_lines(lines, text_width, default_color):
        y = start_y + dy
        if y < height - 1:
            window.addstr(y, padding, line.ljust(text_width), color)
            highlight_hashtags(window, y, padding, line)

    return y + 1
