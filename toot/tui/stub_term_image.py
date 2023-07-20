from __future__ import annotations
from abc import ABCMeta
import urwid

""" This is a stub implementation of the term-image classes
    that the TUI requires to display images.
    It is only used when the term-image library cannot be loaded.
    Class definitions derived from term-image v0.8.0
"""


def auto_image_class() -> ImageMeta:
    return ImageMeta


class ClassPropertyBase(property):
    """Base class for owner properties that also have a counterpart/shadow on the
    instance.
    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        super().__init__(fget, fset, fdel, doc)
        # `property` doesn't set `__doc__`, probably cos the subclass' `__doc__`
        # attribute overrides its `__doc__` descriptor.
        super().__setattr__("__doc__", doc or fget.__doc__)


class ClassProperty(ClassPropertyBase):
    """A read-only shadow of a property of the owner.

    Operation on the owner is actually implemented by a property defined on the
    owner's metaclass. This class is only for the sake of ease of documentation
    without having to bother the user about metaclasses.
    """


class ImageMeta(ABCMeta):
    """Type of all render style classes."""

    _forced_support: bool = False

    forced_support = ClassProperty(
        lambda self: self._forced_support,
        doc="""Forced render style support

        See the base instance of this metaclass for the complete description.
        """,
    )

    @forced_support.setter
    def forced_support(self, status: bool):
        self._forced_support = status


class BaseImage(metaclass=ImageMeta):
    def __init__(self, image, *, width=None, height=None) -> None:
        pass


class GraphicsImage(BaseImage):
    pass


class UrwidImage(urwid.Widget):
    def __init__(self, image: BaseImage, format_spec: str = "", *, upscale: bool = False) -> None:
        pass


def AutoImage(image, *, width=None, height=None) -> BaseImage:
    pass
