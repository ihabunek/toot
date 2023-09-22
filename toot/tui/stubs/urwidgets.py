# If urwidgets is loaded use it; otherwise use our stubs
try:
    from urwidgets import Hyperlink, TextEmbed, parse_text
    has_urwidgets = True
except ImportError:
    from .stub_hyperlink import Hyperlink
    from .stub_text_embed import TextEmbed, parse_text
    has_urwidgets = False
