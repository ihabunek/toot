"""
urWIDgets

A collection of widgets for urwid (https://urwid.org)
"""

__all__ = (
    "parse_text",
    "Hyperlink",
    "TextEmbed",
    # Type Aliases
    "Markup",
    "StringMarkup",
    "ListMarkup",
    "TupleMarkup",
    "NormalTupleMarkup",
    "DisplayAttribute",
    "WidgetTupleMarkup",
    "WidgetListMarkup",
)
__author__ = "Toluwaleke Ogundipe"

from .hyperlink import Hyperlink
from .text_embed import (
    DisplayAttribute,
    ListMarkup,
    Markup,
    NormalTupleMarkup,
    StringMarkup,
    TextEmbed,
    TupleMarkup,
    WidgetListMarkup,
    WidgetTupleMarkup,
    parse_text,
)

version_info = (0, 3, 0, "dev")

# Follows https://semver.org/spec/v2.0.0.html
__version__ = ".".join(map(str, version_info[:3]))
if version_info[3:]:
    __version__ += "-" + ".".join(map(str, version_info[3:]))
