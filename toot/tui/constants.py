# name, fg, bg, mono, fg_h, bg_h
PALETTE = [
    # Components
    ('button', 'white', 'black'),
    ('button_focused', 'light gray', 'dark magenta'),
    ('columns_divider', 'white', 'dark blue'),
    ('content_warning', 'white', 'dark magenta'),
    ('editbox', 'white', 'black'),
    ('editbox_focused', 'white', 'dark magenta'),
    ('footer_message', 'dark green', ''),
    ('footer_message_error', 'light red', ''),
    ('footer_status', 'white', 'dark blue'),
    ('footer_status_bold', 'white, bold', 'dark blue'),
    ('header', 'white', 'dark blue'),
    ('header_bold', 'white,bold', 'dark blue'),
    ('intro_bigtext', 'yellow', ''),
    ('intro_smalltext', 'light blue', ''),
    ('poll_bar', 'white', 'dark blue'),
    ('status_list_selected', 'white,bold', 'dark green'),

    # Functional
    ('hashtag', 'light cyan,bold', ''),
    ('hashtag_followed', 'yellow,bold', ''),
    ('link', ',italics', ''),
    ('link_focused', ',italics', 'dark magenta'),
    ('shortcut', 'light blue', ''),
    ('shortcut_highlight', 'white,bold', ''),
    ('warning', 'light red', ''),

    # Colors
    ('bold', ',bold', ''),
    ('blue', 'light blue', ''),
    ('cyan', 'dark cyan', ''),
    ('gray', 'dark gray', ''),
    ('green', 'dark green', ''),
    ('yellow', 'yellow', ''),
    ('red', 'dark red', ''),
]

MONO_PALETTE = [
    # Components
    ('button', 'white', 'black'),
    ('button_focused', 'black', 'white'),
    ('columns_divider', 'white', 'black'),
    ('content_warning', 'white', 'black'),
    ('editbox', 'white', 'black'),
    ('editbox_focused', 'black', 'white'),
    ('footer_message', 'white', 'black'),
    ('footer_message_error', 'white,bold', 'black'),
    ('footer_status', 'black', 'white'),
    ('footer_status_bold', 'black,bold', 'white'),
    ('header', 'black', 'white'),
    ('header_bold', 'black,bold', 'white'),
    ('intro_bigtext', 'white', 'black'),
    ('intro_smalltext', 'white', 'black'),
    ('poll_bar', 'black', 'white'),
    ('status_list_selected', 'black', 'white'),

    # Functional
    ('hashtag_followed', 'white,bold', 'black'),
    ('hashtag', 'white,bold', 'black'),
    ('link', ',italics', 'black'),
    ('link_focused', ',bold,italics', 'black'),
    ('shortcut', 'white', ''),
    ('shortcut_highlight', 'white,bold', ''),

    # Colors
    ('bold', ',bold', 'black'),
    ('blue', 'white', 'black'),
    ('cyan', 'white', 'black'),
    ('gray', 'white', 'black'),
    ('green', 'white', 'black'),
    ('yellow', 'white', 'black'),
    ('red', 'white', 'black'),
    ('warning', 'white,bold', 'black'),
]

VISIBILITY_OPTIONS = [
    ("public", "Public", "Post to public timelines"),
    ("unlisted", "Unlisted", "Do not post to public timelines"),
    ("private", "Private", "Post to followers only"),
    ("direct", "Direct", "Post to mentioned users only"),
]
