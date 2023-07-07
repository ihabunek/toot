# name, fg, bg, mono, fg_h, bg_h
PALETTE = [
    # Components
    ('button', 'white', 'black'),
    ('button_focused', 'light gray', 'dark magenta'),
    ('card_author', 'yellow', ''),
    ('card_title', 'dark green', ''),
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
    ('status_detail_account', 'dark green', ''),
    ('status_detail_bookmarked', 'light red', ''),
    ('status_detail_timestamp', 'light blue', ''),
    ('status_list_account', 'dark green', ''),
    ('status_list_selected', 'white,bold', 'dark green'),
    ('status_list_timestamp', 'light blue', ''),

    # Functional
    ('hashtag', 'light cyan,bold', ''),
    ('hashtag_followed', 'yellow,bold', ''),
    ('link', ',italics', ''),
    ('link_focused', ',italics', 'dark magenta'),
    ('shortcut', 'light blue', ''),
    ('shortcut_highlight', 'white,bold', ''),
    ('warning', 'light red', ''),

    # Visiblity
    ('visibility_public', 'dark gray', ''),
    ('visibility_unlisted', 'white', ''),
    ('visibility_private', 'dark cyan', ''),
    ('visibility_direct', 'yellow', ''),

    # Styles
    ('bold', ',bold', ''),
    ('dim', 'dark gray', ''),
    ('highlight', 'yellow', ''),
    ('success', 'dark green', ''),
]

MONO_PALETTE = [
    # Components
    ('button', 'white', 'black'),
    ('button_focused', 'black', 'white'),
    ('card_author', 'white', ''),
    ('card_title', 'white, bold', ''),
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
    ('status_detail_account', 'white', ''),
    ('status_detail_bookmarked', 'white', ''),
    ('status_detail_timestamp', 'white', ''),
    ('status_list_account', 'white', ''),
    ('status_list_selected', 'white,bold', ''),
    ('status_list_timestamp', 'white', ''),
    ('warning', 'white,bold', 'black'),

    # Functional
    ('hashtag_followed', 'white,bold', ''),
    ('hashtag', 'white,bold', ''),
    ('link', ',italics', ''),
    ('link_focused', ',bold,italics', ''),
    ('shortcut', 'white', ''),
    ('shortcut_highlight', 'white,bold', ''),

    # Visiblity
    ('visibility_public', 'white', ''),
    ('visibility_unlisted', 'white', ''),
    ('visibility_private', 'white', ''),
    ('visibility_direct', 'white', ''),

    # Styles
    ('bold', ',bold', ''),
    ('dim', 'light gray', ''),
    ('highlight', ',bold', ''),
    ('success', '', ''),
]

VISIBILITY_OPTIONS = [
    ("public", "Public", "Post to public timelines"),
    ("unlisted", "Unlisted", "Do not post to public timelines"),
    ("private", "Private", "Post to followers only"),
    ("direct", "Direct", "Post to mentioned users only"),
]
