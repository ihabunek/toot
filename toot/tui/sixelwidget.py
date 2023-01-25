from typing import Tuple, List, Optional, Any, Iterable
import math
import urwid
from PIL import Image
from libsixel import (
    sixel_output_new,
    sixel_dither_new,
    sixel_dither_initialize,
    sixel_encode,
    sixel_dither_unref,
    sixel_output_unref,
    sixel_dither_get,
    sixel_dither_set_palette,
    sixel_dither_set_pixelformat,
    SIXEL_PIXELFORMAT_RGBA8888,
    SIXEL_PIXELFORMAT_G1,
    SIXEL_PIXELFORMAT_PAL8,
    SIXEL_BUILTIN_G8,
    SIXEL_PIXELFORMAT_G8,
    SIXEL_PIXELFORMAT_RGB888,
    SIXEL_BUILTIN_G1,
)

from io import BytesIO


class SIXELGraphicsCanvas(urwid.canvas.Canvas):
    cacheable = False
    _change_state = 0

    def __init__(
        self, size: Tuple[int, int], img: Image, cell_width: int, cell_height: int
    ) -> None:
        super().__init__()

        self.maxcol = size[0]
        if len(size) > 1:
            self.maxrow = size[1]

        self.img = img
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.text_lines = []

    def cols(self) -> int:
        return self.maxcol

    def rows(self) -> int:
        return self.maxrow

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

        ansi_save_cursor = "\x1b7"
        ansi_restore_cursor = "\x1b8"

        if trim_left > 0:
            trim_left_pix = min(trim_left * self.cell_width, self.img.size[0])
        else:
            trim_left_pix = 0

        trim_img = self.img.crop(
            (
                trim_left_pix,
                self.cell_height * trim_top,
                self.img.size[0],
                self.cell_height * (trim_top + rows),
            )
        )

        sixels = six_encode(trim_img)
        img_cols = math.ceil(trim_img.size[0] / self.cell_width)

        firstTime = True
        for i in range(rows):
            if firstTime:
                text = ansi_save_cursor + sixels + ansi_restore_cursor
                text_bytes = text.encode("utf-8")
                padding = f"\x1b[{img_cols}C" + " " * (cols - img_cols)
                padding = padding.encode("utf-8")
                firstTime = False
            else:
                text_bytes = b""
                padding = f"\x1b[{img_cols}C" + " " * (cols - img_cols)
                padding = padding.encode("utf-8")

            line = [(None, "U", text_bytes + padding)]
            yield line


class SIXELGraphicsWidget(urwid.Widget):
    _sizing = frozenset([urwid.widget.BOX])
    ignore_focus = True

    def __init__(self, img: Image, cell_width: int, cell_height: int) -> None:
        self.img = img
        self.cell_width = cell_width
        self.cell_height = cell_height

    def set_content(self, img: Image) -> None:
        self.img = img
        self.text_lines = []
        self._invalidate()

    def render(self, size: Tuple[int, int], focus: bool = False) -> urwid.canvas.Canvas:
        return SIXELGraphicsCanvas(size, self.img, self.cell_width, self.cell_height)


def six_encode(image: Image) -> str:

    s = BytesIO()

    width, height = image.size
    data = image.tobytes()
    output = sixel_output_new(lambda data, s: s.write(data), s)
    sixel_str = ""

    try:
        if image.mode == "RGBA":
            dither = sixel_dither_new(256)
            sixel_dither_initialize(
                dither, data, width, height, SIXEL_PIXELFORMAT_RGBA8888
            )
        elif image.mode == "RGB":
            dither = sixel_dither_new(256)
            sixel_dither_initialize(
                dither, data, width, height, SIXEL_PIXELFORMAT_RGB888
            )
        elif image.mode == "P":
            palette = image.getpalette()
            dither = sixel_dither_new(256)
            sixel_dither_set_palette(dither, palette)
            sixel_dither_set_pixelformat(dither, SIXEL_PIXELFORMAT_PAL8)
        elif image.mode == "L":
            dither = sixel_dither_get(SIXEL_BUILTIN_G8)
            sixel_dither_set_pixelformat(dither, SIXEL_PIXELFORMAT_G8)
        elif image.mode == "1":
            dither = sixel_dither_get(SIXEL_BUILTIN_G1)
            sixel_dither_set_pixelformat(dither, SIXEL_PIXELFORMAT_G1)
        else:
            raise RuntimeError("unexpected image mode")
        try:
            sixel_encode(data, width, height, 1, dither, output)
            sixel_str = s.getvalue().decode("ascii")
        finally:
            sixel_dither_unref(dither)
    finally:
        sixel_output_unref(output)
        return sixel_str
