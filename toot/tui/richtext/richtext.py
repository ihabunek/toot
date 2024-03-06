import re
import urwid
import unicodedata

from bs4.element import NavigableString, Tag
from toot.tui.constants import PALETTE
from toot.utils import parse_html, urlencode_url
from typing import List, Tuple
from urwid.util import decompose_tagmarkup
from urwidgets import Hyperlink, TextEmbed


STYLE_NAMES = [p[0] for p in PALETTE]

# NOTE: update this list if Mastodon starts supporting more block tags
BLOCK_TAGS = ["p", "pre", "li", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6"]


def html_to_widgets(html, recovery_attempt=False) -> List[urwid.Widget]:
    """Convert html to urwid widgets"""
    widgets: List[urwid.Widget] = []
    html = unicodedata.normalize("NFKC", html)
    soup = parse_html(html)

    first_tag = True
    for e in soup.body or soup:
        if isinstance(e, NavigableString):
            if first_tag and not recovery_attempt:
                # if our first "tag" is a navigable string
                # the HTML is out of spec, doesn't start with a tag,
                # we see this in content from Pixelfed servers.
                # attempt a fix by wrapping the HTML with <p></p>
                return html_to_widgets(f"<p>{html}</p>", recovery_attempt=True)
            else:
                continue
        else:
            name = e.name
            # if our HTML starts with a tag, but not a block tag
            # the HTML is out of spec. Attempt a fix by wrapping the
            # HTML with <p></p>
            if (first_tag and not recovery_attempt and name not in BLOCK_TAGS):
                return html_to_widgets(f"<p>{html}</p>", recovery_attempt=True)

            markup = render(name, e)
            first_tag = False

        if not isinstance(markup, urwid.Widget):
            # plaintext, so create a padded text widget
            txt = text_to_widget("", markup)
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


def url_to_widget(url: str):
    widget = len(url), urwid.Filler(Hyperlink(url, "link", url))
    return TextEmbed(widget)


def inline_tag_to_text(tag) -> Tuple:
    """Convert html tag to plain text with tag as attributes recursively"""
    markups = process_inline_tag_children(tag)
    if not markups:
        return (tag.name, "")
    return (tag.name, markups)


def process_inline_tag_children(tag) -> List:
    """Recursively retrieve all children
    and convert to a list of markup text"""
    markups = []
    for child in tag.children:
        if isinstance(child, Tag):
            markup = render(child.name, child)
            markups.append(markup)
        else:
            markups.append(child)
    return markups


URL_PATTERN = re.compile(r"(^.+)\x03(.+$)")


def text_to_widget(attr, markup) -> urwid.Widget:
    markup_list = []
    for run in markup:
        if isinstance(run, tuple):
            txt, attr_list = decompose_tagmarkup(run)
            # find anchor titles with an ETX separator followed by href
            match = URL_PATTERN.match(txt)
            if match:
                label, url = match.groups()
                anchor_attr = get_best_anchor_attr(attr_list)
                markup_list.append((
                    len(label),
                    urwid.Filler(Hyperlink(url, anchor_attr, label)),
                ))
            else:
                markup_list.append(run)
        else:
            markup_list.append(run)

    return TextEmbed(markup_list)


def process_block_tag_children(tag) -> List[urwid.Widget]:
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
            result = render(child.name, child)
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
        widget_list.append(text_to_widget(tag.name, pre_widget_markups))

    if len(child_widgets):
        widget_list += child_widgets

    if len(post_widget_markups):
        widget_list.append(text_to_widget(tag.name, post_widget_markups))

    return widget_list


def get_urwid_attr_name(tag) -> str:
    """Get the class name and translate to a
    name suitable for use as an urwid
    text attribute name"""

    if "class" in tag.attrs:
        clss = tag.attrs["class"]
        if len(clss) > 0:
            style_name = "class_" + "_".join(clss)
            # return the class name, only if we
            # find it as a defined palette name
            if style_name in STYLE_NAMES:
                return style_name

    # fallback to returning the tag name
    return tag.name


def basic_block_tag_handler(tag) -> urwid.Widget:
    """default for block tags that need no special treatment"""
    return urwid.Pile(process_block_tag_children(tag))


def get_best_anchor_attr(attrib_list) -> str:
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


def render(attr: str, content: str):
    if attr in ["a"]:
        return render_anchor(content)

    if attr in ["blockquote"]:
        return render_blockquote(content)

    if attr in ["br"]:
        return render_br(content)

    if attr in ["em"]:
        return render_em(content)

    if attr in ["ol"]:
        return render_ol(content)

    if attr in ["pre"]:
        return render_pre(content)

    if attr in ["span"]:
        return render_span(content)

    if attr in ["b", "strong"]:
        return render_strong(content)

    if attr in ["ul"]:
        return render_ul(content)

    # Glitch-soc and Pleroma allow <H1>...<H6> in content
    # Mastodon (PR #23913) does not; header tags are converted to <P><STRONG></STRONG></P>
    if attr in ["p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6"]:
        return basic_block_tag_handler(content)

    # Fall back to inline_tag_to_text handler
    return inline_tag_to_text(content)


def render_anchor(tag) -> Tuple:
    """anchor tag handler"""

    markups = process_inline_tag_children(tag)
    if not markups:
        return (tag.name, "")

    href = tag.attrs["href"]
    title, attrib_list = decompose_tagmarkup(markups)
    if not attrib_list:
        attrib_list = [tag]
    if href:
        # urlencode the path and query portions of the URL
        href = urlencode_url(href)
        # use ASCII ETX (end of record) as a
        # delimiter between the title and the HREF
        title += f"\x03{href}"

    attr = get_best_anchor_attr(attrib_list)

    if attr == "a":
        # didn't find an attribute to use
        # in the child markup, so let's
        # try the anchor tag's own attributes

        attr = get_urwid_attr_name(tag)

    # hashtag anchors have a class of "mention hashtag"
    # or "hashtag"
    # we'll return style "class_mention_hashtag"
    # or "class_hashtag"
    # in that case; see corresponding palette entry
    # in constants.py controlling hashtag highlighting

    return (attr, title)


def render_blockquote(tag) -> urwid.Widget:
    widget_list = process_block_tag_children(tag)
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


def render_br(tag) -> Tuple:
    return ("br", "\n")


def render_em(tag) -> Tuple:
    # to simplify the number of palette entries
    # translate EM to I (italic)
    markups = process_inline_tag_children(tag)
    if not markups:
        return ("i", "")

    # special case processing for bold and italic
    for parent in tag.parents:
        if parent.name == "b" or parent.name == "strong":
            return ("bi", markups)

    return ("i", markups)


def render_ol(tag) -> urwid.Widget:
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
        markup = render("li", li)

        # li value= attribute will change the item number
        # it also overrides any ol start= attribute

        if li.has_attr("value") and len(li.attrs["value"]) > 0:
            try:
                list_item_num = int(li.attrs["value"])
            except ValueError:
                pass

        if not isinstance(markup, urwid.Widget):
            txt = text_to_widget("li", [str(list_item_num), ". ", markup])
            # 1. foo, 2. bar, etc.
            widgets.append(txt)
        else:
            txt = text_to_widget("li", [str(list_item_num), ". "])
            columns = urwid.Columns(
                [txt, ("weight", 9999, markup)], dividechars=1, min_width=3
            )
            widgets.append(columns)

        list_item_num += increment

    return urwid.Pile(widgets)


def render_pre(tag) -> urwid.Widget:
    # <PRE> tag spec says that text should not wrap,
    # but horizontal screen space is at a premium
    # and we have no horizontal scroll bar, so allow
    # wrapping.

    widget_list = [urwid.Divider(" ")]
    widget_list += process_block_tag_children(tag)

    pre_widget = urwid.Padding(
        urwid.Pile(widget_list),
        align="left",
        width=("relative", 100),
        min_width=None,
        left=1,
        right=1,
    )
    return urwid.Pile([urwid.AttrMap(pre_widget, "pre")])


def render_span(tag) -> Tuple:
    markups = process_inline_tag_children(tag)

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

        style_name = get_urwid_attr_name(tag)

        if style_name != "span":
            # unique class name matches an entry in our palette
            return (style_name, markups)

    if tag.parent:
        return (get_urwid_attr_name(tag.parent), markups)
    else:
        # fallback
        return ("span", markups)


def render_strong(tag) -> Tuple:
    # to simplify the number of palette entries
    # translate STRONG to B (bold)
    markups = process_inline_tag_children(tag)
    if not markups:
        return ("b", "")

    # special case processing for bold and italic
    for parent in tag.parents:
        if parent.name == "i" or parent.name == "em":
            return ("bi", markups)

    return ("b", markups)


def render_ul(tag) -> urwid.Widget:
    """unordered list tag handler"""

    widgets = []

    for li in tag.find_all("li", recursive=False):
        markup = render("li", li)

        if not isinstance(markup, urwid.Widget):
            txt = text_to_widget("li", ["\N{bullet} ", markup])
            # * foo, * bar, etc.
            widgets.append(txt)
        else:
            txt = text_to_widget("li", ["\N{bullet} "])
            columns = urwid.Columns(
                [txt, ("weight", 9999, markup)], dividechars=1, min_width=3
            )
            widgets.append(columns)

    return urwid.Pile(widgets)


def flatten(data):
    if isinstance(data, tuple):
        for x in data:
            yield from flatten(x)
    else:
        yield data
