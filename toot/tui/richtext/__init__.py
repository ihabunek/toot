import urwid

from toot.tui.utils import highlight_hashtags
from toot.utils import format_content
from typing import List

try:
    from .richtext import html_to_widgets, url_to_widget
except ImportError:
    # Fallback if urwidgets are not available
    def html_to_widgets(html: str) -> List[urwid.Widget]:
        return [
            urwid.Text(highlight_hashtags(line))
            for line in format_content(html)
        ]

    def url_to_widget(url: str):
        return urwid.Text(("link", url))
