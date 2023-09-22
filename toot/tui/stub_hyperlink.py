__all__ = ("Hyperlink",)

from typing import Generator, List, Optional, Tuple, Union

import urwid

# NOTE: Any new "private" attribute of any subclass of an urwid class should be
# prepended with "_uw" to avoid clashes with names used by urwid itself.


ESC = "\033"
OSC = f"{ESC}]"
ST = f"{ESC}\\"
START = f"{OSC}8;id=%d;%s{ST}".encode()
END = f"{OSC}8;;{ST}".encode()

valid_byte_range = range(32, 127)


class Hyperlink(urwid.WidgetWrap):
    """A widget containing hyperlinked text.

    Args:
        uri: The target of the hyperlink in URI (Uniform Resource Identifier)-encoded
          form.

          May be a web address (``http://...`` or ``https://...``), FTP address
          (``ftp://...``), local file (``file://...``), e-mail address (``mailto:``),
          etc.

          Every byte of this string, after being encoded, must be within the range
          ``32`` to ``126`` (both inclusive).

        attr: Display attribute of the hyperlink text.
        text: Alternative hyperlink text. If not given or ``None``, the URI itself is
          used. Must be a single-line string.

    Raises:
        TypeError: An argument is of an unexpected type.
        ValueError: An argument is of an expected type but of an unexpected value

    This widget always renders a single line. If the widget is rendered with a width
    less than the length of the hyperlink text, it is clipped at the right end with an
    ellipsis (\u2026) appended. On the other hand, if rendered with a width greater,
    it is padded with spaces on the right end.

    This widget is intended to be embedded in a :py:class:`~urwidgets.TextEmbed` widget
    to combine it with pure text or other widgets but may also be used otherwise.

    This widget utilizes the ``OSC 8`` escape sequence implemented by a sizable number
    of mainstream terminal emulators. It utilizes the escape sequence in such a way that
    hyperlinks right next to one another should be detected, highlighted and treated as
    separate by any terminal emulator that correctly implements the feature. Also, if a
    hyperlink is wrapped or clipped, it shouldn't break.

    .. seealso::
        - `OSC 8 Specification
          <https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda>`_
        - `OSC 8 adoption in terminal emulators
          <https://github.com/Alhadis/OSC8-Adoption>`_
    """

    no_cache = ["render"]

    def __init__(
        self,
        uri: str,
        attr: Union[None, str, bytes, urwid.AttrSpec] = None,
        text: Optional[str] = None,
    ) -> None:
        self._uw_set_uri(uri)
        super().__init__(urwid.Text((attr, ""), "left", "ellipsis"))
        self._uw_set_text(text or uri)

    def render(self, size: Tuple[int, ], focus: bool = False):
        return None

    def _uw_set_text(self, text: str):
        if not isinstance(text, str):
            raise TypeError(f"Invalid type for 'text' (got: {type(text).__name__!r})")
        if "\n" in text:
            raise ValueError(f"Multi-line text (got: {text!r})")
        self._w.set_text(((self._w.attrib or [(None, 0)])[0][0], text))

    def _uw_set_uri(self, uri: str):
        if not isinstance(uri, str):
            raise TypeError(f"Invalid type for 'uri' (got: {type(uri).__name__!r})")
        if not uri:
            raise ValueError("URI is empty")
        invalid_bytes = frozenset(uri.encode()).difference(valid_byte_range)
        if invalid_bytes:
            raise ValueError(
                f"Invalid byte '\\x{tuple(invalid_bytes)[0]:02x}' found in URI: {uri!r}"
            )
        self._uw_uri = uri

    attrib = property(
        lambda self: (self._w.attrib or [(None, 0)])[0][0],
        lambda self, attrib: self._w.set_text((attrib, self._w.text)),
        doc="""The display attirbute of the hyperlink.

        :type: Union[None, str, bytes, urwid.AttrSpec]

        GET:
            Returns the display attirbute.

        SET:
            Sets the display attirbute.
        """,
    )

    text = property(
        lambda self: self._w.text,
        _uw_set_text,
        doc="""The alternate text of the hyperlink.

        :type: str

        GET:
            Returns the alternate text.

        SET:
            Sets the alternate text.
        """,
    )

    uri = property(
        lambda self: self._uw_uri,
        _uw_set_uri,
        doc="""The target of the hyperlink.

        :type: str

        GET:
            Returns the target.

        SET:
            Sets the target.
        """,
    )


class HyperlinkCanvas(urwid.Canvas):
    cacheable = False

    _uw_next_id = 0
    _uw_free_ids = set()

    def __init__(self, uri: str, text_canv: urwid.TextCanvas) -> None:
        super().__init__()
        self._uw_text_canv = text_canv
        self._uw_uri = uri.encode()
        self._uw_id = self._uw_get_id()

    def __del__(self):
        __class__._uw_free_ids.add(self._uw_id)

    def cols(self):
        return self._uw_text_canv.cols()

    def content(
        self, *args, **kwargs
    ) -> Generator[
        List[Tuple[Union[None, str, bytes, urwid.AttrSpec], Optional[str], bytes]],
        None,
        None,
    ]:
        yield [
            (None, "U", START % (self._uw_id, self._uw_uri)),
            # There can be only one line since wrap="ellipsis" and the text was checked
            # to not contain "\n".
            # There can be only one run since there was only one display attribute.
            next(self._uw_text_canv.content(*args, **kwargs))[0],
            (None, "U", END),
        ]

    def rows(self):
        return self._uw_text_canv.rows()

    def _uw_get_id():
        if __class__._uw_free_ids:
            return __class__._uw_free_ids.pop()
        __class__._uw_next_id += 1

        return __class__._uw_next_id - 1
