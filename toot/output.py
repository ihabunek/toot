# -*- coding: utf-8 -*-

import os
import re
import sys

from datetime import datetime, timezone
from textwrap import wrap
from wcwidth import wcswidth
from toot.tui.utils import parse_datetime

from toot.utils import format_content, get_text, parse_html
from toot.wcstring import wc_wrap


START_CODES = {
    'red': '\033[31m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'magenta': '\033[35m',
    'cyan': '\033[36m',
}

END_CODE = '\033[0m'

START_PATTERN = "<(" + "|".join(START_CODES.keys()) + ")>"

END_PATTERN = "</(" + "|".join(START_CODES.keys()) + ")>"


def start_code(match):
    name = match.group(1)
    return START_CODES[name]


def colorize(text):
    text = re.sub(START_PATTERN, start_code, text)
    text = re.sub(END_PATTERN, END_CODE, text)

    return text


def strip_tags(text):
    text = re.sub(START_PATTERN, '', text)
    text = re.sub(END_PATTERN, '', text)

    return text


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
    args = ["<red>{}</red>".format(a) for a in args]
    args = [colorize(a) if USE_ANSI_COLOR else strip_tags(a) for a in args]
    print(*args, file=sys.stderr, **kwargs)


def print_instance(instance):
    print_out("<green>{}</green>".format(instance['title']))
    print_out("<blue>{}</blue>".format(instance['uri']))
    print_out("running Mastodon {}".format(instance['version']))
    print_out("")

    description = instance['description'].strip()
    if not description:
        return

    lines = [line.strip() for line in format_content(description) if line.strip()]
    for line in lines:
        for l in wrap(line.strip()):
            print_out(l)
        print_out()


def print_account(account):
    print_out("<green>@{}</green> {}".format(account['acct'], account['display_name']))

    note = get_text(account['note'])

    if note:
        print_out("")
        print_out("\n".join(wrap(note)))

    print_out("")
    print_out("ID: <green>{}</green>".format(account['id']))
    print_out("Since: <green>{}</green>".format(account['created_at'][:19].replace('T', ' @ ')))
    print_out("")
    print_out("Followers: <yellow>{}</yellow>".format(account['followers_count']))
    print_out("Following: <yellow>{}</yellow>".format(account['following_count']))
    print_out("Statuses: <yellow>{}</yellow>".format(account['statuses_count']))
    print_out("")
    print_out(account['url'])


HASHTAG_PATTERN = re.compile(r'(?<!\w)(#\w+)\b')


def highlight_hashtags(line):
    return re.sub(HASHTAG_PATTERN, '<cyan>\\1</cyan>', line)

def print_acct_list(accounts):
    for account in accounts:
        print_out("* <green>@{}</green> {}".format(
            account['acct'],
            account['display_name']
        ))

def print_search_results(results):
    accounts = results['accounts']
    hashtags = results['hashtags']

    if accounts:
        print_out("\nAccounts:")
        print_acct_list(accounts)

    if hashtags:
        print_out("\nHashtags:")
        print_out(", ".join(["<green>#{}</green>".format(t["name"]) for t in hashtags]))

    if not accounts and not hashtags:
        print_out("<yellow>Nothing found</yellow>")


def print_status(status, width):
    reblog = status['reblog']
    content = reblog['content'] if reblog else status['content']
    media_attachments = reblog['media_attachments'] if reblog else status['media_attachments']
    in_reply_to = status['in_reply_to_id']

    time = parse_datetime(status['created_at'])
    time = time.strftime('%Y-%m-%d %H:%M %Z')

    username = "@" + status['account']['acct']
    spacing = width - wcswidth(username) - wcswidth(time)

    display_name = status['account']['display_name']
    if display_name:
        spacing -= wcswidth(display_name) + 1

    print_out("{}{}{}{}".format(
        "<green>{}</green> ".format(display_name) if display_name else "",
        "<blue>{}</blue>".format(username),
        " " * spacing,
        "<yellow>{}</yellow>".format(time),
    ))

    for paragraph in parse_html(content):
        print_out("")
        for line in paragraph:
            for subline in wc_wrap(line, width):
                print_out(highlight_hashtags(subline))

    if media_attachments:
        print_out("\nMedia:")
        for attachment in media_attachments:
            url = attachment['text_url'] or attachment['url']
            for line in wc_wrap(url, width):
                print_out(line)

    print_out("\n{}{}{}".format(
        "ID <yellow>{}</yellow>  ".format(status['id']),
        "↲ In reply to <yellow>{}</yellow>  ".format(in_reply_to) if in_reply_to else "",
        "↻ Reblogged <blue>@{}</blue>  ".format(reblog['account']['acct']) if reblog else "",
    ))


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
