from pypandoc import convert_text
from typing import List


def html_to_text(html: str, columns=80, highlight_tags=False) -> List:
    return [convert_text(
        html,
        format="html",
        to="gfm-raw_html",
        extra_args=["--wrap=auto", f"--columns={columns}"],
    )]
