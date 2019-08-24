from urwid.command_map import command_map
from urwid.command_map import CURSOR_UP, CURSOR_DOWN, CURSOR_LEFT, CURSOR_RIGHT

# Add movement using h/j/k/l to default command map
command_map._command.update({
    'k': CURSOR_UP,
    'j': CURSOR_DOWN,
    'h': CURSOR_LEFT,
    'l': CURSOR_RIGHT,
})
