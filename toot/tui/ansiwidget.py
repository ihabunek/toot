from typing import Tuple, List, Optional, Any, Iterable
import logging
import re
import urwid
from PIL import Image

logger = logging.getLogger("toot")


class ANSIGraphicsCanvas(urwid.canvas.Canvas):
    def __init__(self, size: Tuple[int, int], img: Image) -> None:
        super().__init__()

        self.maxcol = size[0]
        if len(size) > 1:
            self.maxrow = size[1]

        self.img = img
        self.text_lines = []

        # for performance, these regexes are simplified
        # and only match the ANSI escapes we generate
        # in the content(...) method below.
        self.ansi_escape = re.compile(r"\x1b[^m]*m")
        self.ansi_escape_capture = re.compile(r"(\x1b[^m]*m)")

    def cols(self) -> int:
        return self.maxcol

    def rows(self) -> int:
        return self.maxrow

    def strip_ansi_codes(self, ansi_text):
        return self.ansi_escape.sub("", ansi_text)

    def truncate_ansi_safe(self, ansi_text, trim_left, maxlength):
        if len(self.strip_ansi_codes(ansi_text)) <= maxlength:
            return ansi_text

        trunc_text = ""
        real_len = 0
        token_pt_len = 0

        for token in re.split(self.ansi_escape_capture, ansi_text):
            if token and token[0] == "\x1b":
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
        trim_left: int = 0,
        trim_top: int = 0,
        cols: Optional[int] = None,
        rows: Optional[int] = None,
        attr_map: Optional[Any] = None,
    ) -> Iterable[List[Tuple[None, str, bytes]]]:

        maxcol, maxrow = self.cols(), self.rows()
        if not cols:
            cols = maxcol - trim_left
        if not rows:
            rows = maxrow - trim_top

        assert trim_left >= 0 and trim_left < maxcol
        assert cols > 0 and trim_left + cols <= maxcol
        assert trim_top >= 0 and trim_top < maxrow
        assert rows > 0 and trim_top + rows <= maxrow

        ansi_reset = "\x1b[0m".encode("utf-8")

        if len(self.text_lines) == 0:
            width, height = self.img.size
            pixels = self.img.load()
            if (self.img.mode == 'P'):
                # palette-mode image; 256 colors or fewer
                for y in range(1, height - 1, 2):
                    line = ""
                    for x in range(1, width):
                        pa = pixels[x, y]
                        pb = pixels[x, y + 1]
                        # render via unicode half-blocks, 256 color ANSI syntax
                        line += f"\x1b[48;5;{pa}m\x1b[38;5;{pb}m\u2584"
                    self.text_lines.append(line)
            else:
                # truecolor image (RGB)
                # note: we don't attempt to support mode 'L' greyscale images
                # nor do we support mode '1' single bit depth images.
                for y in range(1, height - 1, 2):
                    line = ""
                    for x in range(1, width):
                        ra, ga, ba = pixels[x, y]
                        rb, gb, bb = pixels[x, y + 1]
                        # render via unicode half-blocks, truecolor ANSI syntax
                        line += f"\x1b[48;2;{ra};{ga};{ba}m\x1b[38;2;{rb};{gb};{bb}m\u2584"
                    self.text_lines.append(line)

        if trim_top or rows <= self.maxrow:
            self.render_lines = self.text_lines[trim_top:trim_top + rows]
        else:
            self.render_lines = self.text_lines

        for i in range(rows):
            if i < len(self.render_lines):
                text = self.truncate_ansi_safe(
                    self.render_lines[i], trim_left, cols - 1
                )
                real_len = len(self.strip_ansi_codes(text))
                text_bytes = text.encode("utf-8")
            else:
                text_bytes = b""
                real_len = 0

            padding = bytes().rjust(max(0, cols - real_len))
            line = [(None, "U", text_bytes + ansi_reset + padding)]
            yield line


class ANSIGraphicsWidget(urwid.Widget):
    _sizing = frozenset([urwid.widget.BOX])
    ignore_focus = True

    def __init__(self, img: Image) -> None:
        self.img = img

    def set_content(self, img: Image) -> None:
        self.img = img
        self.text_lines = []
        self._invalidate()

    def render(self, size: Tuple[int, int], focus: bool = False) -> urwid.canvas.Canvas:
        return ANSIGraphicsCanvas(size, self.img)
