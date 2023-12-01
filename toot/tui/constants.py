# Color definitions are tuples of:
#   - name
#   - foreground (normal mode)
#   - background (normal mode)
#   - foreground (monochrome mode)
#   - foreground (high color mode)
#   - background (high color mode)
#
# See:
# http://urwid.org/tutorial/index.html#display-attributes
# http://urwid.org/manual/displayattributes.html#using-display-attributes

PALETTE = [
    # Components
    ('button', 'white', 'black'),
    ('button_focused', 'light gray', 'dark magenta', 'bold,underline'),
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
    ('header_bold', 'white,bold', 'dark blue', 'bold'),
    ('intro_bigtext', 'yellow', ''),
    ('intro_smalltext', 'light blue', ''),
    ('poll_bar', 'white', 'dark blue'),
    ('status_detail_account', 'dark green', ''),
    ('status_detail_bookmarked', 'light red', ''),
    ('status_detail_timestamp', 'light blue', ''),
    ('status_list_account', 'dark green', ''),
    ('status_list_selected', 'white,bold', 'dark green', 'bold,underline'),
    ('status_list_timestamp', 'light blue', ''),

    # Functional
    ('account', 'dark green', ''),
    ('hashtag', 'light cyan,bold', '', 'bold'),
    ('hashtag_followed', 'yellow,bold', '', 'bold'),
    ('link', ',italics', '', ',italics'),
    ('link_focused', ',italics', 'dark magenta', "underline,italics"),
    ('shortcut', 'light blue', ''),
    ('shortcut_highlight', 'white,bold', '', 'bold'),
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

    # HTML tag styling
    ('a', ',italics', '', 'italics'),
    # em tag is mapped to i
    ('i', ',italics', '', 'italics'),
    # strong tag is mapped to b
    ('b', ',bold', '', 'bold'),
    # special case for bold + italic nested tags
    ('bi', ',bold,italics', '', ',bold,italics'),
    ('u', ',underline', '', ',underline'),
    ('del', ',strikethrough', '', ',strikethrough'),
    ('code', 'light gray, standout', '', ',standout'),
    ('pre', 'light gray, standout', '', ',standout'),
    ('blockquote', 'light gray', '', ''),
    ('h1', ',bold', '', ',bold'),
    ('h2', ',bold', '', ',bold'),
    ('h3', ',bold', '', ',bold'),
    ('h4', ',bold', '', ',bold'),
    ('h5', ',bold', '', ',bold'),
    ('h6', ',bold', '', ',bold'),
    ('class_mention_hashtag', 'light cyan', '', ''),
    ('class_hashtag', 'light cyan', '', ''),

]

VISIBILITY_OPTIONS = [
    ("public", "Public", "Post to public timelines"),
    ("unlisted", "Unlisted", "Do not post to public timelines"),
    ("private", "Private", "Post to followers only"),
    ("direct", "Direct", "Post to mentioned users only"),
]
