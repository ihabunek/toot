import re

from toot.wcstring import fit_text, wc_wrap


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
                for wrapped in wc_wrap(line, text_width):
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


def size_as_drawn(lines, screen_width):
    """Get the bottom-right corner of some text as would be drawn by draw_lines"""
    y = 0
    x = 0
    for line in lines:
        wrapped = list(wc_wrap(line, screen_width))
        if len(wrapped) > 0:
            for wrapped_line in wrapped:
                x = len(wrapped_line)
                y += 1
        else:
            x = 0
            y += 1
    return y - 1, x - 1 if x != 0 else 0


def draw_lines(window, lines, start_y, padding, default_color):
    height, width = window.getmaxyx()
    text_width = width - 2 * padding

    for dy, (line, color) in enumerate_lines(lines, text_width, default_color):
        y = start_y + dy
        if y < height - 1:
            window.addstr(y, padding, fit_text(line, text_width), color)
            highlight_hashtags(window, y, padding, line)

    return y + 1
