def draw_horizontal_divider(window, y):
    height, width = window.getmaxyx()

    # Don't draw out of bounds
    if y < height - 1:
        line = '├' + '─' * (width - 2) + '┤'
        window.addstr(y, 0, line)


def enumerate_lines(generator, default_color):
    for y, item in enumerate(generator):
        if isinstance(item, tuple) and len(item) == 2:
            yield y, item[0], item[1]
        elif isinstance(item, str):
            yield y, item, default_color
        elif item is None:
            yield y, "", default_color
        else:
            raise ValueError("Wrong yield in generator")


def draw_lines(window, lines, x, y, default_color):
    height, _ = window.getmaxyx()
    for dy, line, color in enumerate_lines(lines, default_color):
        if y + dy < height - 1:
            window.addstr(y + dy, x, line, color)

    return y + dy + 1
