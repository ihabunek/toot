# If term_image is loaded use their screen implementation which handles images
try:
    from term_image.widget import UrwidImageScreen
    from term_image import disable_queries  # prevent phantom keystrokes
    TuiScreen = UrwidImageScreen
    disable_queries()
except ImportError:
    from urwid.raw_display import Screen
    TuiScreen = Screen
