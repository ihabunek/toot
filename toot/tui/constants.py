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
    ('white_bold', 'white,bold', ''),

    # HTML tag styling
    # note, anchor styling is often overridden
    # by class names in Mastodon statuses
    # so you won't see the italics.
    ('a', ',italics', ''),
    ('em', 'white,italics', ''),
    ('i', 'white,italics', ''),
    ('strong', 'white,bold', ''),
    ('b', 'white,bold', ''),
    ('u', 'white,underline', ''),
    ('del', 'white, strikethrough', ''),
    ('code', 'white, standout', ''),
    ('pre', 'white, standout', ''),
    ('blockquote', 'light gray', ''),
    ('h1', 'white, bold', ''),
    ('h2', 'white, bold', ''),
    ('h3', 'white, bold', ''),
    ('h4', 'white, bold', ''),
    ('h5', 'white, bold', ''),
    ('h6', 'white, bold', ''),
    ('class_mention_hashtag', 'light cyan,bold', ''),

]

VISIBILITY_OPTIONS = [
    ("public", "Public", "Post to public timelines"),
    ("unlisted", "Unlisted", "Do not post to public timelines"),
    ("private", "Private", "Post to followers only"),
    ("direct", "Direct", "Post to mentioned users only"),
]
