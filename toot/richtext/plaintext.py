from toot.utils import html_to_paragraphs
from toot.wcstring import wc_wrap
from toot.tui.utils import highlight_hashtags
from typing import List


def html_to_plaintext(html: str, columns=80, highlight_tags=False) -> List:
    output = []
    first = True
    for paragraph in html_to_paragraphs(html):
        if not first:
            output.append("")
        for line in paragraph:
            for subline in wc_wrap(line, columns):
                if highlight_tags:
                    output.append(highlight_hashtags(subline))
                else:
                    output.append(subline)
        first = False
    return output
