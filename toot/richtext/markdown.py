from toot.exceptions import ConsoleError
from pypandoc import convert_text
from toot.richtext.plaintext import html_to_plaintext
from typing import List


def html_to_text(html: str, columns=80, render_mode: str = "", highlight_tags=False) -> List:
    if render_mode == "plaintext":
        return html_to_plaintext(html, columns, highlight_tags)
    elif render_mode == "markdown" or render_mode == "":
        return [convert_text(
            html,
            format="html",
            to="gfm-raw_html",
            extra_args=["--wrap=auto", f"--columns={columns}"],
        )]
    raise ConsoleError("Unknown render mode; specify 'plaintext' or 'markdown'")
