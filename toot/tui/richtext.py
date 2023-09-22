"""
richtext
"""
from typing import List, Tuple
import re
import urwid
import unicodedata
from .constants import PALETTE
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from .stubs.urwidgets import TextEmbed, Hyperlink, parse_text, has_urwidgets
from urwid.util import decompose_tagmarkup
from toot.utils import urlencode_url


class ContentParser:
    def __init__(self):
        self.palette_names = []
        for p in PALETTE:
            self.palette_names.append(p[0])

        """Parse a limited subset of HTML and create urwid widgets."""

    def html_to_widgets(self, html, recovery_attempt=False) -> List[urwid.Widget]:
        """Convert html to urwid widgets"""
        widgets: List[urwid.Widget] = []
        html = unicodedata.normalize("NFKC", html)
        soup = BeautifulSoup(html.replace("&apos;", "'"), "html.parser")
        first_tag = True
        for e in soup.body or soup:
            if isinstance(e, NavigableString):
                if first_tag and not recovery_attempt:
                    # if our first "tag" is a navigable string
                    # the HTML is out of spec, doesn't start with a tag,
                    # we see this in content from Pixelfed servers.
                    # attempt a fix by wrapping the HTML with <p></p>
                    return self.html_to_widgets(f"<p>{html}</p>", recovery_attempt=True)
                else:
                    continue
            else:
                name = e.name
                # if our HTML starts with a tag, but not a block tag
                # the HTML is out of spec. Attempt a fix by wrapping the
                # HTML with <p></p>
                if (
                    first_tag
                    and not recovery_attempt
                    and name
                    not in (
                        "p",
                        "pre",
                        "li",
                        "blockquote",
                        "h1",
                        "h2",
                        "h3",
                        "h4",
                        "h5",
                        "h6",
                    )  # NOTE: update this list if Mastodon starts supporting more block tags
                ):
                    return self.html_to_widgets(f"<p>{html}</p>", recovery_attempt=True)

                # First, look for a custom tag handler method in this class
                # If that fails, fall back to inline_tag_to_text handler
                method = getattr(self, "_" + name, self.inline_tag_to_text)
                markup = method(e)  # either returns a Widget, or plain text
                first_tag = False

            if not isinstance(markup, urwid.Widget):
                # plaintext, so create a padded text widget
                txt = self.text_to_widget("", markup)
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

    def inline_tag_to_text(self, tag) -> Tuple:
        """Convert html tag to plain text with tag as attributes recursively"""
        markups = self.process_inline_tag_children(tag)
        if not markups:
            return (tag.name, "")
        return (tag.name, markups)

    def process_inline_tag_children(self, tag) -> List:
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

    def text_to_widget(self, attr, markup) -> urwid.Widget:
        if not has_urwidgets:
            return urwid.Text((attr, markup))

        TRANSFORM = {
            # convert http[s] URLs to Hyperlink widgets for nesting in a TextEmbed widget
            re.compile(r"(^.+)\x03(.+$)"): lambda g: (
                len(g[1]),
                urwid.Filler(Hyperlink(g[2], anchor_attr, g[1])),
            ),
        }
        markup_list = []

        for run in markup:
            if isinstance(run, tuple):
                txt, attr_list = decompose_tagmarkup(run)
                # find anchor titles with an ETX separator followed by href
                m = re.match(r"(^.+)\x03(.+$)", txt)
                if m:
                    anchor_attr = self.get_best_anchor_attr(attr_list)
                    markup_list.append(
                        parse_text(
                            txt,
                            TRANSFORM,
                            lambda pattern, groups, span: TRANSFORM[pattern](groups),
                        )
                    )
                else:
                    markup_list.append(run)
            else:
                markup_list.append(run)

        return TextEmbed(markup_list)

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
            widget_list.append(self.text_to_widget(tag.name, pre_widget_markups))

        if len(child_widgets):
            widget_list += child_widgets

        if len(post_widget_markups):
            widget_list.append(self.text_to_widget(tag.name, post_widget_markups))

        return widget_list

    def get_urwid_attr_name(self, tag) -> str:
        """Get the class name and translate to a
        name suitable for use as an urwid
        text attribute name"""

        if "class" in tag.attrs:
            clss = tag.attrs["class"]
            if len(clss) > 0:
                style_name = "class_" + "_".join(clss)
                # return the class name, only if we
                # find it as a defined palette name
                if style_name in self.palette_names:
                    return style_name

        # fallback to returning the tag name
        return tag.name

    # Tag handlers start here.
    # Tags not explicitly listed are "supported" by
    # rendering as text.
    # Inline tags return a list of marked up text for urwid.Text
    # Block tags return urwid.Widget

    def basic_block_tag_handler(self, tag) -> urwid.Widget:
        """default for block tags that need no special treatment"""
        return urwid.Pile(self.process_block_tag_children(tag))

    def get_best_anchor_attr(self, attrib_list) -> str:
        if not attrib_list:
            return ""
        flat_al = list(flatten(attrib_list))

        for a in flat_al[0]:
            # ref: https://docs.joinmastodon.org/spec/activitypub/
            # these are the class names (translated to attrib names)
            # that we can support for display

            try:
                if a[0] in ["class_hashtag", "class_mention_hashtag", "class_mention"]:
                    return a[0]
            except KeyError:
                continue

        return "a"

    def _a(self, tag) -> Tuple:
        """anchor tag handler"""

        markups = self.process_inline_tag_children(tag)
        if not markups:
            return (tag.name, "")

        href = tag.attrs["href"]
        title, attrib_list = decompose_tagmarkup(markups)
        if not attrib_list:
            attrib_list = [tag]
        if href and has_urwidgets:
            # only if we have urwidgets loaded for OCS 8 hyperlinks:
            # urlencode the path and query portions of the URL
            href = urlencode_url(href)
            # use ASCII ETX (end of record) as a
            # delimiter between the title and the HREF
            title += f"\x03{href}"

        attr = self.get_best_anchor_attr(attrib_list)

        if attr == "a":
            # didn't find an attribute to use
            # in the child markup, so let's
            # try the anchor tag's own attributes

            attr = self.get_urwid_attr_name(tag)

        # hashtag anchors have a class of "mention hashtag"
        # or "hashtag"
        # we'll return style "class_mention_hashtag"
        # or "class_hashtag"
        # in that case; see corresponding palette entry
        # in constants.py controlling hashtag highlighting

        return (attr, title)

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

    def _br(self, tag) -> Tuple:
        return ("br", "\n")

    def _em(self, tag) -> Tuple:
        # to simplify the number of palette entries
        # translate EM to I (italic)
        markups = self.process_inline_tag_children(tag)
        if not markups:
            return ("i", "")

        # special case processing for bold and italic
        for parent in tag.parents:
            if parent.name == "b" or parent.name == "strong":
                return ("bi", markups)

        return ("i", markups)

    def _ol(self, tag) -> urwid.Widget:
        """ordered list tag handler"""

        widgets = []
        list_item_num = 1
        increment = -1 if tag.has_attr("reversed") else 1

        # get ol start= attribute if present
        if tag.has_attr("start") and len(tag.attrs["start"]) > 0:
            try:
                list_item_num = int(tag.attrs["start"])
            except ValueError:
                pass

        for li in tag.find_all("li", recursive=False):
            method = getattr(self, "_li", self.inline_tag_to_text)
            markup = method(li)

            # li value= attribute will change the item number
            # it also overrides any ol start= attribute

            if li.has_attr("value") and len(li.attrs["value"]) > 0:
                try:
                    list_item_num = int(li.attrs["value"])
                except ValueError:
                    pass

            if not isinstance(markup, urwid.Widget):
                txt = self.text_to_widget("li", [str(list_item_num), ". ", markup])
                # 1. foo, 2. bar, etc.
                widgets.append(txt)
            else:
                txt = self.text_to_widget("li", [str(list_item_num), ". "])
                columns = urwid.Columns(
                    [txt, ("weight", 9999, markup)], dividechars=1, min_width=3
                )
                widgets.append(columns)

            list_item_num += increment

        return urwid.Pile(widgets)

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

    def _span(self, tag) -> Tuple:
        markups = self.process_inline_tag_children(tag)

        if not markups:
            return (tag.name, "")

        # span inherits its parent's class definition
        # unless it has a specific class definition
        # of its own

        if "class" in tag.attrs:
            # uncomment the following code to hide all HTML marked
            # invisible (generally, the http:// prefix of URLs)
            # could be a user preference, it's only advisable if
            # the terminal supports OCS 8 hyperlinks (and that's not
            # automatically detectable)

            # if "invisible" in tag.attrs["class"]:
            #     return (tag.name, "")

            style_name = self.get_urwid_attr_name(tag)

            if style_name != "span":
                # unique class name matches an entry in our palette
                return (style_name, markups)

        if tag.parent:
            return (self.get_urwid_attr_name(tag.parent), markups)
        else:
            # fallback
            return ("span", markups)

    def _strong(self, tag) -> Tuple:
        # to simplify the number of palette entries
        # translate STRONG to B (bold)
        markups = self.process_inline_tag_children(tag)
        if not markups:
            return ("b", "")

        # special case processing for bold and italic
        for parent in tag.parents:
            if parent.name == "i" or parent.name == "em":
                return ("bi", markups)

        return ("b", markups)

    def _ul(self, tag) -> urwid.Widget:
        """unordered list tag handler"""

        widgets = []

        for li in tag.find_all("li", recursive=False):
            method = getattr(self, "_li", self.inline_tag_to_text)
            markup = method(li)

            if not isinstance(markup, urwid.Widget):
                txt = self.text_to_widget("li", ["\N{bullet} ", markup])
                # * foo, * bar, etc.
                widgets.append(txt)
            else:
                txt = self.text_to_widget("li", ["\N{bullet} "])
                columns = urwid.Columns(
                    [txt, ("weight", 9999, markup)], dividechars=1, min_width=3
                )
                widgets.append(columns)

        return urwid.Pile(widgets)

    # These tags are handled identically to others
    # the only difference being the tag name used for
    # urwid attribute mapping

    _b = _strong

    _div = basic_block_tag_handler

    _i = _em

    _li = basic_block_tag_handler

    # Glitch-soc and Pleroma allow <H1>...<H6> in content
    # Mastodon (PR #23913) does not; header tags are converted to <P><STRONG></STRONG></P>

    _h1 = _h2 = _h3 = _h4 = _h5 = _h6 = basic_block_tag_handler

    _p = basic_block_tag_handler


def flatten(data):
    if isinstance(data, tuple):
        for x in data:
            yield from flatten(x)
    else:
        yield data
