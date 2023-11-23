import urwid
from pypandoc import convert_text

from typing import List

def url_to_widget(url: str):
    return urwid.Text(("link", url))

def html_to_widgets(html: str) -> List[urwid.Widget]:
    return [
        urwid.Text(
            convert_text(
                html,
                format="html",
                to="gfm-raw_html",
                extra_args=["--wrap=none"],
            )
        )
    ]
