__all__ = ("parse_text", "TextEmbed")

import urwid


class TextEmbed(urwid.Text):
    def get_text(self):
        return None

    def render(self, size, focus):
        return None

    def set_text(self, markup):
        pass

    def set_wrap_mode(self, mode):
        pass


def parse_text(text, patterns, repl, *repl_args, **repl_kwargs):
    return None
