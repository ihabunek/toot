import urwid
import html2text

from typing import List

try:
    from .richtext import html_to_widgets, url_to_widget
except ImportError:
    # Fallback if urwidgets are not available
    def html_to_widgets(html: str) -> List[urwid.Widget]:
        return [
            urwid.Text(_format_markdown(html))
        ]

    def url_to_widget(url: str):
        return urwid.Text(("link", url))

    def _format_markdown(html) -> str:
        h2t = html2text.HTML2Text()
        h2t.single_line_break = True
        h2t.ignore_links = True
        h2t.wrap_links = False
        h2t.wrap_list_items = False
        h2t.wrap_tables = False
        h2t.unicode_snob = True
        h2t.ul_item_mark = "\N{bullet}"
        return h2t.handle(html).strip()
