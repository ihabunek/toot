import os
import re
import sys
import textwrap

from functools import lru_cache
from toot import settings
from toot.utils import get_text, html_to_paragraphs
from toot.entities import Account, Instance, Notification, Poll, Status
from toot.wcstring import wc_wrap
from typing import Iterable, List
from wcwidth import wcswidth


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


@lru_cache(maxsize=None)
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

    # Check in settings
    color = settings.get_setting("common.color", bool)
    if color is not None:
        return color

    # Use color by default
    return True


def print_out(*args, **kwargs):
    if not settings.get_quiet():
        args = [colorize(a) if use_ansi_color() else strip_tags(a) for a in args]
        print(*args, **kwargs)


def print_err(*args, **kwargs):
    args = [f"<red>{a}</red>" for a in args]
    args = [colorize(a) if use_ansi_color() else strip_tags(a) for a in args]
    print(*args, file=sys.stderr, **kwargs)


def print_instance(instance: Instance):
    print_out(f"<green>{instance.title}</green>")
    print_out(f"<blue>{instance.uri}</blue>")
    print_out(f"running Mastodon {instance.version}")
    print_out()

    if instance.description:
        for paragraph in re.split(r"[\r\n]+", instance.description.strip()):
            paragraph = get_text(paragraph)
            print_out(textwrap.fill(paragraph, width=80))
            print_out()

    if instance.rules:
        print_out("Rules:")
        for ordinal, rule in enumerate(instance.rules):
            ordinal = f"{ordinal + 1}."
            lines = textwrap.wrap(rule.text, 80 - len(ordinal))
            first = True
            for line in lines:
                if first:
                    print_out(f"{ordinal} {line}")
                    first = False
                else:
                    print_out(f"{' ' * len(ordinal)} {line}")
        print_out()

    contact = instance.contact_account
    if contact:
        print_out(f"Contact: {contact.display_name} @{contact.acct}")


def print_account(account: Account):
    print_out(f"<green>@{account.acct}</green> {account.display_name}")

    if account.note:
        print_out("")
        print_html(account.note)

    since = account.created_at.strftime('%Y-%m-%d')

    print_out("")
    print_out(f"ID: <green>{account.id}</green>")
    print_out(f"Since: <green>{since}</green>")
    print_out("")
    print_out(f"Followers: <yellow>{account.followers_count}</yellow>")
    print_out(f"Following: <yellow>{account.following_count}</yellow>")
    print_out(f"Statuses: <yellow>{account.statuses_count}</yellow>")

    if account.fields:
        for field in account.fields:
            name = field.name.title()
            print_out(f'\n<yellow>{name}</yellow>:')
            print_html(field.value)
            if field.verified_at:
                print_out("<green>✓ Verified</green>")

    print_out("")
    print_out(account.url)


HASHTAG_PATTERN = re.compile(r'(?<!\w)(#\w+)\b')


def highlight_hashtags(line):
    return re.sub(HASHTAG_PATTERN, '<cyan>\\1</cyan>', line)


def print_acct_list(accounts):
    for account in accounts:
        print_out(f"* <green>@{account['acct']}</green> {account['display_name']}")


def print_user_list(users):
    for user in users:
        print_out(f"* {user}")


def print_tag_list(tags):
    if tags:
        for tag in tags:
            print_out(f"* <green>#{tag['name']}\t</green>{tag['url']}")
    else:
        print_out("You're not following any hashtags.")


def print_lists(lists):
    headers = ["ID", "Title", "Replies"]
    data = [[lst["id"], lst["title"], lst["replies_policy"]] for lst in lists]
    print_table(headers, data)


def print_table(headers: List[str], data: List[List[str]]):
    widths = [[len(cell) for cell in row] for row in data + [headers]]
    widths = [max(width) for width in zip(*widths)]

    def style(string, tag):
        return f"<{tag}>{string}</{tag}>" if tag else string

    def print_row(row, tag=None):
        for idx, cell in enumerate(row):
            width = widths[idx]
            print_out(style(cell.ljust(width), tag), end="")
            print_out("  ", end="")
        print_out()

    underlines = ["-" * width for width in widths]

    print_row(headers, "bold")
    print_row(underlines, "dim")

    for row in data:
        print_row(row)


def print_list_accounts(accounts):
    if accounts:
        print_out("Accounts in list</green>:\n")
        print_acct_list(accounts)
    else:
        print_out("This list has no accounts.")


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


def print_status(status: Status, width: int = 80):
    status_id = status.id
    in_reply_to_id = status.in_reply_to_id
    reblogged_by = status.account if status.reblog else None

    status = status.original

    time = status.created_at.strftime('%Y-%m-%d %H:%M %Z')
    username = "@" + status.account.acct
    spacing = width - wcswidth(username) - wcswidth(time) - 2

    display_name = status.account.display_name
    if display_name:
        spacing -= wcswidth(display_name) + 1

    print_out(
        f"<green>{display_name}</green>" if display_name else "",
        f"<blue>{username}</blue>",
        " " * spacing,
        f"<yellow>{time}</yellow>",
    )

    print_out("")
    print_html(status.content, width)

    if status.media_attachments:
        print_out("\nMedia:")
        for attachment in status.media_attachments:
            url = attachment.url
            for line in wc_wrap(url, width):
                print_out(line)

    if status.poll:
        print_poll(status.poll)

    print_out()

    print_out(
        f"ID <yellow>{status_id}</yellow> ",
        f"↲ In reply to <yellow>{in_reply_to_id}</yellow> " if in_reply_to_id else "",
        f"↻ <blue>@{reblogged_by.acct}</blue> boosted " if reblogged_by else "",
    )


def print_html(text, width=80):
    first = True
    for paragraph in html_to_paragraphs(text):
        if not first:
            print_out("")
        for line in paragraph:
            for subline in wc_wrap(line, width):
                print_out(highlight_hashtags(subline))
        first = False


def print_poll(poll: Poll):
    print_out()
    for idx, option in enumerate(poll.options):
        perc = (round(100 * option.votes_count / poll.votes_count)
            if poll.votes_count and option.votes_count is not None else 0)

        if poll.voted and poll.own_votes and idx in poll.own_votes:
            voted_for = " <yellow>✓</yellow>"
        else:
            voted_for = ""

        print_out(f'{option.title} - {perc}% {voted_for}')

    poll_footer = f'Poll · {poll.votes_count} votes'

    if poll.expired:
        poll_footer += " · Closed"

    if poll.expires_at:
        expires_at = poll.expires_at.strftime("%Y-%m-%d %H:%M")
        poll_footer += f" · Closes on {expires_at}"

    print_out()
    print_out(poll_footer)


def print_timeline(items: Iterable[Status], width=100):
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


def print_notification(notification: Notification, width=100):
    account = f"{notification.account.display_name} @{notification.account.acct}"
    msg = notification_msgs.get(notification.type)
    if msg is None:
        return

    print_out("─" * width)
    print_out(msg.format(account=account))
    if notification.status:
        print_status(notification.status, width)


def print_notifications(notifications: List[Notification], width=100):
    for notification in notifications:
        print_notification(notification)
    print_out("─" * width)
