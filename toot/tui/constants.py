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

    # Functional
    ('hashtag', 'light cyan,bold', ''),
    ('followed_hashtag', 'yellow,bold', ''),
    ('link', ',italics', ''),
    ('link_focused', ',italics', 'dark magenta'),

    # Colors
    ('bold', ',bold', ''),
    ('blue', 'light blue', ''),
    ('blue_bold', 'light blue, bold', ''),
    ('blue_selected', 'white', 'dark blue'),
    ('cyan', 'dark cyan', ''),
    ('cyan_bold', 'dark cyan,bold', ''),
    ('gray', 'dark gray', ''),
    ('green', 'dark green', ''),
    ('green_selected', 'white,bold', 'dark green'),
    ('yellow', 'yellow', ''),
    ('yellow_bold', 'yellow,bold', ''),
    ('red', 'dark red', ''),
    ('warning', 'light red', ''),
    ('white_bold', 'white,bold', '')
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

    # Functional
    ('hashtag', 'white,bold', 'black'),
    ('followed_hashtag', 'white,bold', 'black'),
    ('link', ',italics', 'black'),
    ('link_focused', ',bold,italics', 'black'),

    # Colors
    ('bold', ',bold', 'black'),
    ('blue', 'white', 'black'),
    ('blue_bold', 'white, bold', 'black'),
    ('blue_selected', 'white, bold', 'black'),
    ('cyan', 'white', 'black'),
    ('cyan_bold', 'white,bold', 'black'),
    ('gray', 'white', 'black'),
    ('green', 'white', 'black'),
    ('green_selected', 'black', 'white'),
    ('yellow', 'white', 'black'),
    ('yellow_bold', 'white,bold', 'black'),
    ('red', 'white', 'black'),
    ('warning', 'white,bold', 'black'),
    ('white_bold', 'white,bold', 'black')
]

VISIBILITY_OPTIONS = [
    ("public", "Public", "Post to public timelines"),
    ("unlisted", "Unlisted", "Do not post to public timelines"),
    ("private", "Private", "Post to followers only"),
    ("direct", "Direct", "Post to mentioned users only"),
]
