# If urwidgets is loaded use it; otherwise use our stubs
try:
    from urwidgets import Hyperlink, TextEmbed, parse_text  # noqa: F401
    has_urwidgets = True
except ImportError:
    from .stub_hyperlink import Hyperlink  # noqa: F401
    from .stub_text_embed import TextEmbed, parse_text  # noqa: F401
    has_urwidgets = False
