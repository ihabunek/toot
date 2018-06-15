# -*- coding: utf-8 -*-

import sys
import re

from bs4 import BeautifulSoup
from datetime import datetime
from itertools import chain
from itertools import zip_longest
from textwrap import wrap, TextWrapper

from toot.utils import format_content, get_text, trunc

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


USE_ANSI_COLOR = "--no-color" not in sys.argv
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


def print_search_results(results):
    accounts = results['accounts']
    hashtags = results['hashtags']

    if accounts:
        print_out("\nAccounts:")
        for account in accounts:
            print_out("* <green>@{}</green> {}".format(
                account['acct'],
                account['display_name']
            ))

    if hashtags:
        print_out("\nHashtags:")
        print_out(", ".join(["<green>#{}</green>".format(t) for t in hashtags]))

    if not accounts and not hashtags:
        print_out("<yellow>Nothing found</yellow>")


def print_timeline(items):
    def _print_item(item):
        def wrap_text(text, width):
            wrapper = TextWrapper(width=width, break_long_words=False, break_on_hyphens=False)
            return chain(*[wrapper.wrap(l) for l in text.split("\n")])

        def timeline_rows(item):
            display_name = item['account']['display_name']
            username = "@" + item['account']['username']
            time = item['time'].strftime('%Y-%m-%d %H:%M%Z')

            left_column = [display_name]
            if display_name != username:
                left_column.append(username)
            left_column.append(time)
            if item['reblogged']:
                left_column.append("Reblogged @{}".format(item['reblogged']))

            right_column = wrap_text(item['text'], 80)

            return zip_longest(left_column, right_column, fillvalue="")

        for left, right in timeline_rows(item):
            print_out("{:30} │ {}".format(trunc(left, 30), right))

    def _parse_item(item):
        content = item['reblog']['content'] if item['reblog'] else item['content']
        reblogged = item['reblog']['account']['username'] if item['reblog'] else None

        soup = BeautifulSoup(content, "html.parser")
        text = soup.get_text().replace('&apos;', "'")
        time = datetime.strptime(item['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ")

        return {
            "account": item['account'],
            "text": text,
            "time": time,
            "reblogged": reblogged,
        }

    print_out("─" * 31 + "┬" + "─" * 88)
    for item in items:
        _print_item(_parse_item(item))
        print_out("─" * 31 + "┼" + "─" * 88)
