from urwid import Divider, Filler, Pile
from toot.tui.richtext import url_to_widget
from urwidgets import Hyperlink, TextEmbed

from toot.tui.richtext.richtext import html_to_widgets


def test_url_to_widget():
    url = "http://foo.bar"
    embed_widget = url_to_widget(url)
    assert isinstance(embed_widget, TextEmbed)

    [(filler, length)] = embed_widget.embedded
    assert length == len(url)
    assert isinstance(filler, Filler)

    link_widget = filler.base_widget
    assert isinstance(link_widget, Hyperlink)

    assert link_widget.attrib == "link"
    assert link_widget.text == url
    assert link_widget.uri == url


def test_html_to_widgets():
    html = """
    <p>foo</p>
    <p>foo <b>bar</b> <i>baz</i></p>
    """.strip()

    [foo, divider, bar] = html_to_widgets(html)

    assert isinstance(foo, Pile)
    assert isinstance(divider, Divider)
    assert isinstance(bar, Pile)

    [(foo_embed, _)] = foo.contents
    assert foo_embed.embedded == []
    assert foo_embed.attrib == []
    assert foo_embed.text == "foo"

    [(bar_embed, _)] = bar.contents
    assert bar_embed.embedded == []
    assert bar_embed.attrib == [(None, 4), ("b", 3), (None, 1), ("i", 3)]
    assert bar_embed.text == "foo bar baz"
