"""
richtext
"""
from typing import List
import urwid
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag


class ContentParser:
    def __init__(self, config={}):
        """Parse a limited subset of HTML and create urwid widgets."""

    def html_to_widgets(self, html) -> List[urwid.Widget]:
        """Convert html to urwid widgets"""
        widgets: List[urwid.Widget] = []
        soup = BeautifulSoup(html.replace("&apos;", "'"), "html.parser")
        for e in soup.body or soup:
            if isinstance(e, NavigableString):
                continue
            name = e.name
            # First, look for a custom tag handler method in this class
            # If that fails, fall back to inline_tag_to_text handler
            method = getattr(self, "_" + name, self.inline_tag_to_text)
            markup = method(e)  # either returns a Widget, or plain text

            if not isinstance(markup, urwid.Widget):
                # plaintext, so create a padded text widget
                txt = urwid.Text(markup)
                markup = urwid.Padding(
                    txt,
                    align="left",
                    width=("relative", 100),
                    min_width=None,
                )
            widgets.append(markup)
            # separate top level widgets with a blank line
            widgets.append(urwid.Divider(" "))
        return widgets[:-1]  # but suppress the last blank line

    def inline_tag_to_text(self, tag) -> list:
        """Convert html tag to plain text with tag as attributes recursively"""
        markups = self.process_inline_tag_children(tag)
        if not markups:
            return ""
        return (tag.name, markups)

    def process_inline_tag_children(self, tag) -> list:
        """Recursively retrieve all children
        and convert to a list of markup text"""
        markups = []
        for child in tag.children:
            if isinstance(child, Tag):
                method = getattr(self, "_" + child.name, self.inline_tag_to_text)
                markup = method(child)
                markups.append(markup)
            else:
                markups.append(child)
        return markups

    def process_block_tag_children(self, tag) -> List[urwid.Widget]:
        """Recursively retrieve all children
        and convert to a list of widgets
        any inline tags containing text will be
        converted to Text widgets"""

        pre_widget_markups = []
        post_widget_markups = []
        child_widgets = []
        found_nested_widget = False

        for child in tag.children:
            if isinstance(child, Tag):
                # child is a nested tag; process using custom method
                # or default to inline_tag_to_text
                method = getattr(self, "_" + child.name, self.inline_tag_to_text)
                result = method(child)
                if isinstance(result, urwid.Widget):
                    found_nested_widget = True
                    child_widgets.append(result)
                else:
                    if not found_nested_widget:
                        pre_widget_markups.append(result)
                    else:
                        post_widget_markups.append(result)
            else:
                # child is text; append to the appropriate markup list
                if not found_nested_widget:
                    pre_widget_markups.append(child)
                else:
                    post_widget_markups.append(child)

        widget_list = []
        if len(pre_widget_markups):
            widget_list.append(urwid.Text((tag.name, pre_widget_markups)))

        if len(child_widgets):
            widget_list += child_widgets

        if len(post_widget_markups):
            widget_list.append(urwid.Text((tag.name, post_widget_markups)))

        return widget_list

    def get_urwid_attr_name(self, tag) -> str:
        """Get the class name and translate to a
        name suitable for use as an urwid
        text attribute name"""
        # TODO: think about whitelisting allowed classes,
        # or blacklisting classes we do not want.
        # Classes to whitelist: "mention" "hashtag"
        # used in anchor tags
        # Classes to blacklist: "invisible" used in Akkoma
        # anchor titles

        if "class" in tag.attrs:
            clss = tag.attrs["class"]
            if len(clss) > 0:
                style_name = "class_" + "_".join(clss)
                return style_name

        style_name = tag.name

    # Tag handlers start here.
    # Tags not explicitly listed are "supported" by
    # rendering as text.
    # Inline tags return a list of marked up text for urwid.Text
    # Block tags return urwid.Widget

    def basic_block_tag_handler(self, tag) -> urwid.Widget:
        """default for block tags that need no special treatment"""
        return urwid.Pile(self.process_block_tag_children(tag))

    def _a(self, tag) -> list:
        markups = self.process_inline_tag_children(tag)
        if not markups:
            return ""

        # hashtag anchors have a class of "mention hashtag"
        # we'll return style "class_mention_hashtag"
        # in that case; set this up in constants.py
        # to control highlighting of hashtags

        return (self.get_urwid_attr_name(tag), markups)

    def _blockquote(self, tag) -> urwid.Widget:
        widget_list = self.process_block_tag_children(tag)
        blockquote_widget = urwid.LineBox(
            urwid.Padding(
                urwid.Pile(widget_list),
                align="left",
                width=("relative", 100),
                min_width=None,
                left=1,
                right=1,
            ),
            tlcorner="",
            tline="",
            lline="│",
            trcorner="",
            blcorner="",
            rline="",
            bline="",
            brcorner="",
        )
        return urwid.Pile([urwid.AttrMap(blockquote_widget, "blockquote")])

    def _br(self, tag) -> list:
        return (tag.name, ("br", "\n"))

    _div = basic_block_tag_handler

    _li = basic_block_tag_handler

    # Glitch-soc and Pleroma allow <H1>...<H6> in content
    # Mastodon (PR #23913) does not; header tags are converted to <P><STRONG></STRONG></P>

    _h1 = _h2 = _h3 = _h4 = _h5 = _h6 = basic_block_tag_handler

    def _ol(self, tag) -> urwid.Widget:
        return self.list_widget(tag, ordered=True)

    _p = basic_block_tag_handler

    def _pre(self, tag) -> urwid.Widget:

        # <PRE> tag spec says that text should not wrap,
        # but horizontal screen space is at a premium
        # and we have no horizontal scroll bar, so allow
        # wrapping.

        widget_list = [urwid.Divider(" ")]
        widget_list += self.process_block_tag_children(tag)

        pre_widget = urwid.Padding(
            urwid.Pile(widget_list),
            align="left",
            width=("relative", 100),
            min_width=None,
            left=1,
            right=1,
        )
        return urwid.Pile([urwid.AttrMap(pre_widget, "pre")])

    def _span(self, tag) -> list:
        markups = self.process_inline_tag_children(tag)

        if not markups:
            return ""

        # span inherits its parent's class definition
        # unless it has a specific class definition
        # of its own

        if "class" in tag.attrs:
            style_name = self.get_urwid_attr_name(tag)
        elif tag.parent:
            style_name = self.get_urwid_attr_name(tag.parent)
        else:
            style_name = tag.name

        return (style_name, markups)

    def _ul(self, tag) -> urwid.Widget:
        return self.list_widget(tag, ordered=False)

    def list_widget(self, tag, ordered=False) -> urwid.Widget:
        """common logic for ordered and unordered list rendering
        as urwid widgets"""
        widgets = []
        i = 1
        for li in tag.find_all("li", recursive=False):
            method = getattr(self, "_li", self.inline_tag_to_text)
            markup = method(li)

            if not isinstance(markup, urwid.Widget):
                if ordered:
                    txt = urwid.Text(
                        ("li", [str(i), ". ", markup])
                    )  # 1. foo, 2. bar, etc.
                else:
                    txt = urwid.Text(("li", ["\N{bullet} ", markup]))  # * foo, * bar, etc.
                widgets.append(txt)
            else:
                if ordered:
                    txt = urwid.Text(("li", [str(i) + "."]))
                else:
                    txt = urwid.Text(("li", "\N{bullet}"))

                columns = urwid.Columns(
                    [txt, ("weight", 9999, markup)], dividechars=1, min_width=3
                )
                widgets.append(columns)
            i += 1

        return urwid.Pile(widgets)
