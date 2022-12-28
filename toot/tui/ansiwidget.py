from typing import Tuple, List, Optional, Any, Iterable

import re
import urwid
from PIL import Image
from colors import color

class ANSIGraphicsCanvas(urwid.canvas.Canvas):
    def __init__(self, size: Tuple[int, int], img: Image) -> None:
        super().__init__()

        self.maxcols = size[0]
        if len(size) > 1:
            self.maxrows = size[1]

        self.img = img
        self.text_lines = []
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        self.ansi_escape_capture = re.compile(r'(\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]))')

    def cols(self) -> int:
        return self.maxcols

    def rows(self) -> int:
        return self.maxrows

    def strip_ansi_codes(self, ansi_text):
        return self.ansi_escape.sub('', ansi_text)

    def truncate_ansi_safe(self, ansi_text, trim_left, maxlength):
        if len(self.strip_ansi_codes(ansi_text)) <= maxlength:
            return ansi_text

        trunc_text = ''
        real_len = 0
        token_pt_len = 0

        for token in re.split(self.ansi_escape_capture, ansi_text):
            if token and token[0] == '\x1b':
                # this token is an ANSI sequence so just add it
                trunc_text += token
            else:
                # this token is plaintext so add chars if we can
                if token_pt_len + len(token) < trim_left:
                    # this token is entirely within trim zone
                    # skip it
                    token_pt_len += len(token)
                    continue
                if token_pt_len < trim_left:
                    # this token is partially within trim zone
                    # partially skip, partially add
                    token_pt_len += len(token)
                    token = token[trim_left - token_pt_len + 1:]

                token_slice = token[:maxlength - real_len + 1]
                trunc_text += token_slice
                real_len += len(token_slice)

            if real_len >= maxlength + trim_left:
                break

        return trunc_text

    def content(
        self,
        trim_left: int = 0, trim_top: int = 0,
        cols: Optional[int] = None, rows: Optional[int] = None,
        attr_map: Optional[Any] = None
    ) -> Iterable[List[Tuple[None, str, bytes]]]:
        assert cols is not None
        assert rows is not None

        ansi_reset = '\x1b[0m'.encode('utf-8')

        self.text_lines = []
        width, height = self.img.size
        for i in range(1, height-1, 2):
            line = ''
            for j in range(1, width):
                    ra, ga, ba = self.img.getpixel((j, i))
                    rb, gb, bb = self.img.getpixel((j, i+1))
                    # render via unicode half-blocks
                    line += color('\u2584', fg=(rb, gb, bb), bg=(ra, ga, ba))
            self.text_lines.append(line)

        if trim_top or rows < self.maxrows:
            self.text_lines = self.text_lines[trim_top:trim_top+rows]

        for i in range(rows):
            if  i < len(self.text_lines):
                text = self.truncate_ansi_safe(self.text_lines[i], trim_left, cols - 1)
                real_len = len(self.strip_ansi_codes(text))
                text_bytes = text.encode('utf-8')
            else:
                text_bytes = b''
                real_len = 0

            padding = bytes().rjust(max(0, cols - real_len))
            line = [(None, 'U', text_bytes + padding + ansi_reset)]
            yield line


class ANSIGraphicsWidget(urwid.Widget):
    _sizing = frozenset([urwid.widget.BOX])
    ignore_focus = True

    def __init__(self, img: Image) -> None:
        urwid.set_encoding('utf8')
        self.img = img

    def set_content(self, img: Image) -> None:
        self.img = img
        self.text_lines = []
        self._invalidate()

    def render(self, size: Tuple[int, int], focus: bool = False) -> urwid.canvas.Canvas:
        return ANSIGraphicsCanvas(size, self.img)
