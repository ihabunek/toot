__all__ = (
    "parse_text",
    "TextEmbed",
    # Type Aliases
    "Markup",
    "StringMarkup",
    "ListMarkup",
    "TupleMarkup",
    "NormalTupleMarkup",
    "DisplayAttribute",
    "WidgetTupleMarkup",
    "WidgetListMarkup",
)

import re
from typing import Any, Iterable, List, Tuple, Union

import urwid

# NOTE: Any new "private" attribute of any subclass of an urwid class should be
# prepended with "_uw" to avoid clashes with names used by urwid itself.

# I really hope these are correct :D
Markup = Union["StringMarkup", "ListMarkup", "TupleMarkup"]
StringMarkup = Union[str, bytes]
ListMarkup = List["Markup"]
TupleMarkup = Union["NormalTupleMarkup", "WidgetTupleMarkup"]
NormalTupleMarkup = Tuple["DisplayAttribute", Union["StringMarkup", "ListMarkup"]]
DisplayAttribute = Union[None, str, bytes, urwid.AttrSpec]
WidgetTupleMarkup = Tuple[int, Union[urwid.Widget, "WidgetListMarkup"]]
WidgetListMarkup = List[Union[urwid.Widget, "Markup", "WidgetListMarkup"]]


class TextEmbed(urwid.Text):
    """A text widget within which other widgets may be embedded.

    This is an extension of the :py:class:`urwid.Text` widget. Every feature and
    interface of :py:class:`~urwid.Text` is supported and works essentially the same,
    **except for the "ellipsis" wrap mode** which is currently not implemented.
    Text markup format is essentially the same, except when embedding widgets.

    **Embedding Widgets**
        A widget is embedded by specifying it as a markup element with an **integer
        display attribute**, where the display attribute is the number of screen
        columns the widget should occupy.

        Examples:

        >>> # w1 spans 2 columns
        >>> TextEmbed(["This widget (", (2, w1), ") spans two columns"])
        >>> # w1 and w2 span 2 columns
        >>> TextEmbed(["These widgets (", (2, [w1, w2]), ") span two columns each"])
        >>> # w1 and w2 span 2 columns, the text in-between has no display attribute
        >>> TextEmbed([(2, [w1, (None, "and"), w2]), " span two columns each"])
        >>> # w1 and w2 span 2 columns, text in the middle is red
        >>> TextEmbed((2, [w1, ("red", " i am red "), w2]))
        >>> # w1 and w3 span 2 columns, w2 spans 5 columns
        >>> TextEmbed((2, [w1, (5, w2), w3]))

        Visible embedded widgets are always rendered (may be cached) whenever the
        ``TextEmbed`` widget is re-rendered (i.e an uncached render). Hence, this
        allows for dynamic parts of text without updating the entire widget.
        Going a step further, embeddded widgets can be swapped by using
        ``urwid.WidgetPlaceholder`` but their widths will remain the same.

        NOTE:
            - Every embedded widget must be a box widget and is always rendered with
              size ``(width, 1)``.  :py:class:`urwid.Filler` can be used to wrap flow
              widgets.
            - Each embedded widgets are treated as a single WORD (i.e containing no
              whitespace). Therefore, consecutive embedded widgets are also treated as
              a single WORD. This affects the "space" wrap mode.
            - After updating or swapping an embedded widget, this widget's canvases
              should be invalidated to ensure it re-renders.

    Raises:
        TypeError: A widget markup element has a non-integer display attribute.
        ValueError: A widget doesn't support box sizing.
        ValueError: A widget has a non-positive width (display attribute).
    """
    def get_text(
        self,
    ) -> Tuple[str, List[Tuple[Union[DisplayAttribute, int], int]]]:
        """Returns a representation of the widget's content.

        Returns:
            A tuple ``(text, attrib)``, where

            - *text* is the raw text content of the widget.

              Each embedded widget is represented by a substring starting with a
              ``"\\x00"`` character followed by zero or more ``"\\x01"`` characters,
              with length equal to the widget's width.

            - *attrib* is the run-length encoding of display attributes.

              Any entry containing a display attribute of the ``int`` type (e.g
              ``(1, 4)``) denotes an embedded widget, where the display attirbute is
              the index of the widget within the :py:attr:`embedded` widgets list and
              the run length is the width of the widget.
        """
        return super().get_text()

    def render(
        self, size: Tuple[int, ], focus: bool = False
    ) -> Union[urwid.TextCanvas, urwid.CompositeCanvas]:
        return None

    def set_text(self, markup: Markup) -> None:
        """Sets the widget's content.

        Also supports widget markup elements. See the class description.
        """
    pass

    def set_wrap_mode(self, mode: str) -> None:
        if mode == "ellipsis":
            raise NotImplementedError("Wrap mode 'ellipsis' is not implemented.")
        super().set_wrap_mode(mode)


def parse_text(
    text: str,
    patterns: Iterable[re.Pattern],
    repl,
    *repl_args: Any,
    **repl_kwargs: Any,
) -> Markup:
    r"""Parses a string into a text/widget markup list.

    Args:
        text: The string to parse.
        patterns: An iterable of RegEx pattern objects.
        repl: A callable to replace a substring of *text* matched by any of the given
          RegEx patterns.
        repl_args: Additional positional arguments to be passed to *repl* whenever it's
          called.
        repl_kwargs: keyword arguments to be passed to *repl* whenever it's called.

    Returns:
        A text/widget markup (see :py:data:`Markup`) that should be compatible with
        :py:class:`TextEmbed` and/or :py:class:`urwid.Text`, depending on the values
        returned by *repl*.

    Raises:
        TypeError: An argument is of an unexpected type.
        ValueError: *patterns* is empty.
        ValueError: A given pattern object was not compiled from a :py:class:`str`
          instance.

    Whenever any of the given RegEx patterns matches a **non-empty** substring of
    *text*, *repl* is called with the following arguments (in the given order):

    - the :py:class:`re.Pattern` object that matched the substring
    - a tuple containing the match groups

      - starting with the whole match,
      - followed by the all the subgroups of the match, from 1 up to however many
        groups are in the pattern, if any (``None`` for each group that didn't
        participate in the match)

    - a tuple containing the indexes of the start and end of the substring
    - *repl_args* unpacked
    - *repl_kwargs* unpacked

    and *should* return a valid text/widget markup (see :py:data:`Markup`). If the
    value returned is *false* (such as ``None`` or an empty string), it is omitted
    from the result.

    Example::

        import re
        from urwid import Filler
        from urwidgets import Hyperlink, TextEmbed, parse_text

        MARKDOWN = {
            re.compile(r"\*\*(.+?)\*\*"): lambda g: ("bold", g[1]),
            re.compile("https://[^ ]+"): (
                lambda g: (min(len(g[0]), 14), Filler(Hyperlink(g[0], "blue")))
            ),
            re.compile(r"\[(.+)\]\((.+)\)"): (
                lambda g: (len(g[1]), Filler(Hyperlink(g[2], "blue", g[1])))
            ),
        }

        link = "https://urwid.org"
        text = f"[This]({link}) is a **link** to {link}"
        print(text)
        # Output: [This](https://urwid.org) is a **link** to https://urwid.org

        markup = parse_text(
            text, MARKDOWN, lambda pattern, groups, span: MARKDOWN[pattern](groups)
        )
        print(markup)
        # Output:
        # [
        #   (4, <Filler box widget <Hyperlink flow widget>>),
        #   ' is a ',
        #   ('bold', 'link'),
        #   ' to ',
        #   (14, <Filler box widget <Hyperlink flow widget>>),
        # ]

        text_widget = TextEmbed(markup)
        canv = text_widget.render(text_widget.pack()[:1])
        print(canv.text[0].decode())
        # Output: This is a link to https://urwid…
        # The hyperlinks will be clickable if supported

    NOTE:
        In the case of overlapping matches, the substring that occurs first is matched
        and if they start at the same index, the pattern that appears first in
        *patterns* takes precedence.
    """
    return text
