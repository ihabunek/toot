# -*- coding: utf-8 -*-

import os
import re
import sys
import textwrap

from textwrap import wrap
from toot.tui.utils import parse_datetime
from wcwidth import wcswidth

from toot.utils import get_text, parse_html
from toot.wcstring import wc_wrap


STYLES = {
    'reset': '\033[0m',
    'bold': '\033[1m',
    'dim': '\033[2m',
    'italic': '\033[3m',
    'underline': '\033[4m',
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'magenta': '\033[95m',
    'cyan': '\033[96m',
}

STYLE_TAG_PATTERN = re.compile(r"""
    (?<!\\)     # not preceeded by a backslash - allows escaping
    <           # literal
    (/)?        # optional closing - first group
    (.*?)       # style names - ungreedy - second group
    >           # literal
""", re.X)


def colorize(message):
    """
    Replaces style tags in `message` with ANSI escape codes.

    Markup is inspired by HTML, but you can use multiple words pre tag, e.g.:

        <red bold>alert!</red bold> a thing happened

    Empty closing tag will reset all styes:

        <red bold>alert!</> a thing happened

    Styles can be nested:

        <red>red <underline>red and underline</underline> red</red>
    """

    def _codes(styles):
        for style in styles:
            yield STYLES.get(style, "")

    def _generator(message):
        # A list is used instead of a set because we want to keep style order
        # This allows nesting colors, e.g. "<blue>foo<red>bar</red>baz</blue>"
        position = 0
        active_styles = []

        for match in re.finditer(STYLE_TAG_PATTERN, message):
            is_closing = bool(match.group(1))
            styles = match.group(2).strip().split()

            start, end = match.span()
            # Replace backslash for escaped <
            yield message[position:start].replace("\\<", "<")

            if is_closing:
                yield STYLES["reset"]

                # Empty closing tag resets all styles
                if styles == []:
                    active_styles = []
                else:
                    active_styles = [s for s in active_styles if s not in styles]
                    yield from _codes(active_styles)
            else:
                active_styles = active_styles + styles
                yield from _codes(styles)

            position = end

        if position == 0:
            # Nothing matched, yield the original string
            yield message
        else:
            # Yield the remaining fragment
            yield message[position:]
            # Reset styles at the end to prevent leaking
            yield STYLES["reset"]

    return "".join(_generator(message))


def strip_tags(message):
    return re.sub(STYLE_TAG_PATTERN, "", message)


def use_ansi_color():
    """Returns True if ANSI color codes should be used."""

    # Windows doesn't support color unless ansicon is installed
    # See: http://adoxa.altervista.org/ansicon/
    if sys.platform == 'win32' and 'ANSICON' not in os.environ:
        return False

    # Don't show color if stdout is not a tty, e.g. if output is piped on
    if not sys.stdout.isatty():
        return False

    # Don't show color if explicitly specified in options
    if "--no-color" in sys.argv:
        return False

    return True


USE_ANSI_COLOR = use_ansi_color()

QUIET = "--quiet" in sys.argv


def print_out(*args, **kwargs):
    if not QUIET:
        args = [colorize(a) if USE_ANSI_COLOR else strip_tags(a) for a in args]
        print(*args, **kwargs)


def print_err(*args, **kwargs):
    args = [f"<red>{a}</red>" for a in args]
    args = [colorize(a) if USE_ANSI_COLOR else strip_tags(a) for a in args]
    print(*args, file=sys.stderr, **kwargs)


def print_instance(instance):
    print_out(f"<green>{instance['title']}</green>")
    print_out(f"<blue>{instance['uri']}</blue>")
    print_out(f"running Mastodon {instance['version']}")
    print_out()

    description = instance.get("description")
    if description:
        for paragraph in re.split(r"[\r\n]+", description.strip()):
            paragraph = get_text(paragraph)
            print_out(textwrap.fill(paragraph, width=80))
            print_out()

    rules = instance.get("rules")
    if rules:
        print_out("Rules:")
        for ordinal, rule in enumerate(rules):
            ordinal = f"{ordinal + 1}."
            lines = textwrap.wrap(rule["text"], 80 - len(ordinal))
            first = True
            for line in lines:
                if first:
                    print_out(f"{ordinal} {line}")
                    first = False
                else:
                    print_out(f"{' ' * len(ordinal)} {line}")


def print_account(account):
    print_out(f"<green>@{account['acct']}</green> {account['display_name']}")

    note = get_text(account['note'])

    if note:
        print_out("")
        print_out("\n".join(wrap(note)))

    print_out("")
    print_out(f"ID: <green>{account['id']}</green>")
    print_out(f"Since: <green>{account['created_at'][:10]}</green>")
    print_out("")
    print_out(f"Followers: <yellow>{account['followers_count']}</yellow>")
    print_out(f"Following: <yellow>{account['following_count']}</yellow>")
    print_out(f"Statuses: <yellow>{account['statuses_count']}</yellow>")
    print_out("")
    print_out(account["url"])


HASHTAG_PATTERN = re.compile(r'(?<!\w)(#\w+)\b')


def highlight_hashtags(line):
    return re.sub(HASHTAG_PATTERN, '<cyan>\\1</cyan>', line)


def print_acct_list(accounts):
    for account in accounts:
        print_out(f"* <green>@{account['acct']}</green> {account['display_name']}")


def print_search_results(results):
    accounts = results['accounts']
    hashtags = results['hashtags']

    if accounts:
        print_out("\nAccounts:")
        print_acct_list(accounts)

    if hashtags:
        print_out("\nHashtags:")
        print_out(", ".join([f"<green>#{t['name']}</green>" for t in hashtags]))

    if not accounts and not hashtags:
        print_out("<yellow>Nothing found</yellow>")


def print_status(status, width):
    reblog = status['reblog']
    content = reblog['content'] if reblog else status['content']
    media_attachments = reblog['media_attachments'] if reblog else status['media_attachments']
    in_reply_to = status['in_reply_to_id']
    poll = reblog.get('poll') if reblog else status.get('poll')

    time = parse_datetime(status['created_at'])
    time = time.strftime('%Y-%m-%d %H:%M %Z')

    username = "@" + status['account']['acct']
    spacing = width - wcswidth(username) - wcswidth(time) - 2

    display_name = status['account']['display_name']
    if display_name:
        spacing -= wcswidth(display_name) + 1

    print_out(
        f"<green>{display_name}</green>" if display_name else "",
        f"<blue>{username}</blue>",
        " " * spacing,
        f"<yellow>{time}</yellow>",
    )

    for paragraph in parse_html(content):
        print_out("")
        for line in paragraph:
            for subline in wc_wrap(line, width):
                print_out(highlight_hashtags(subline))

    if media_attachments:
        print_out("\nMedia:")
        for attachment in media_attachments:
            url = attachment["url"]
            for line in wc_wrap(url, width):
                print_out(line)

    if poll:
        print_poll(poll)

    print_out()
    print_out(
        f"ID <yellow>{status['id']}</yellow> ",
        f"↲ In reply to <yellow>{in_reply_to}</yellow> " if in_reply_to else "",
        f"↻ Reblogged <blue>@{reblog['account']['acct']}</blue> " if reblog else "",
    )


def print_poll(poll):
    print_out()
    for idx, option in enumerate(poll["options"]):
        perc = (round(100 * option["votes_count"] / poll["votes_count"])
            if poll["votes_count"] else 0)

        if poll["voted"] and poll["own_votes"] and idx in poll["own_votes"]:
            voted_for = " <yellow>✓</yellow>"
        else:
            voted_for = ""

        print_out(f'{option["title"]} - {perc}% {voted_for}')

    poll_footer = f'Poll · {poll["votes_count"]} votes'

    if poll["expired"]:
        poll_footer += " · Closed"

    if poll["expires_at"]:
        expires_at = parse_datetime(poll["expires_at"]).strftime("%Y-%m-%d %H:%M")
        poll_footer += f" · Closes on {expires_at}"

    print_out()
    print_out(poll_footer)


def print_timeline(items, width=100):
    print_out("─" * width)
    for item in items:
        print_status(item, width)
        print_out("─" * width)


notification_msgs = {
    "follow": "{account} now follows you",
    "mention": "{account} mentioned you in",
    "reblog": "{account} reblogged your status",
    "favourite": "{account} favourited your status",
}


def print_notification(notification, width=100):
    account = "{display_name} @{acct}".format(**notification["account"])
    msg = notification_msgs.get(notification["type"])
    if msg is None:
        return

    print_out("─" * width)
    print_out(msg.format(account=account))
    status = notification.get("status")
    if status is not None:
        print_status(status, width)


def print_notifications(notifications, width=100):
    for notification in notifications:
        print_notification(notification)
    print_out("─" * width)
