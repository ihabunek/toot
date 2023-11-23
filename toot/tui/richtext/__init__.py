import urwid
from toot.tui.utils import highlight_hashtags
from toot.utils import format_content
from typing import List

try:
    # our first preference is to render using urwidgets
    from .richtext import html_to_widgets, url_to_widget

except ImportError:
    try:
        # second preference, render markup with pypandoc
        from .markdown import html_to_widgets, url_to_widget

    except ImportError:
        # Fallback to render in plaintext

        def url_to_widget(url: str):
            return urwid.Text(("link", url))

        def html_to_widgets(html: str) -> List[urwid.Widget]:
            return [
                urwid.Text(highlight_hashtags(line)) for line in format_content(html)
            ]
