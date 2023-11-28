from toot.exceptions import ConsoleError
from toot.richtext.plaintext import html_to_plaintext
from typing import List

try:
    # first preference, render markup with pypandoc
    from .markdown import html_to_text

except ImportError:
    # Fallback to render in plaintext
    def html_to_text(html: str, columns=80, render_mode: str = "", highlight_tags=False) -> List:
        if render_mode == "markdown":
            raise ConsoleError("Can't render as markdown because the pypandoc library is not available.")

        return html_to_plaintext(html, columns, highlight_tags)
