# If term_image is loaded use their screen implementation which handles images
try:
    from term_image.widget import UrwidImageScreen
    TuiScreen = UrwidImageScreen
    from term_image.image import AutoImage, GraphicsImage, auto_image_class
    from term_image.widget import UrwidImage
    has_term_image = True
except ImportError:
    from urwid.raw_display import Screen
    TuiScreen = Screen
    from .stub_term_image import AutoImage, GraphicsImage, auto_image_class
    from .stub_term_image import UrwidImage
    has_term_image = False
