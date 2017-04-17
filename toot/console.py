# -*- coding: utf-8 -*-
#
from __future__ import print_function

import os
import sys
import logging

from bs4 import BeautifulSoup
from builtins import input
from datetime import datetime
from future.moves.itertools import zip_longest
from getpass import getpass
from itertools import chain
from argparse import ArgumentParser, FileType
from textwrap import TextWrapper

from toot import api, DEFAULT_INSTANCE
from toot.api import ApiError
from toot.config import save_user, load_user, load_app, save_app, CONFIG_APP_FILE, CONFIG_USER_FILE


class ConsoleError(Exception):
    pass


def red(text):
    return u"\033[31m{}\033[0m".format(text)


def green(text):
    return u"\033[32m{}\033[0m".format(text)


def yellow(text):
    return u"\033[33m{}\033[0m".format(text)


def print_error(text):
    print(red(text), file=sys.stderr)


def create_app_interactive():
    instance = input("Choose an instance [%s]: " % green(DEFAULT_INSTANCE))
    if not instance:
        instance = DEFAULT_INSTANCE

    base_url = 'https://{}'.format(instance)

    print("Registering application with %s" % green(base_url))
    try:
        app = api.create_app(base_url)
    except:
        raise ConsoleError("Failed authenticating application. Did you enter a valid instance?")

    save_app(app)
    print("Application tokens saved to: {}".format(green(CONFIG_APP_FILE)))

    return app


def login_interactive(app):
    print("\nLog in to " + green(app.base_url))
    email = input('Email: ')
    password = getpass('Password: ')

    print("Authenticating...")
    try:
        user = api.login(app, email, password)
    except:
        raise ConsoleError("Login failed")

    save_user(user)
    print("User token saved to " + green(CONFIG_USER_FILE))

    return user


def print_usage():
    print("toot - interact with Mastodon from the command line")
    print("")
    print("Usage:")
    print("  toot login      - log into a Mastodon instance (saves access tokens to `~/.config/toot/`)")
    print("  toot logout     - log out (delete saved access tokens)")
    print("  toot auth       - shows currently logged in user and instance")
    print("  toot post <msg> - toot a new post to your timeline")
    print("  toot search     - search for accounts or hashtags")
    print("  toot timeline   - shows your public timeline")
    print("  toot follow     - follow an account")
    print("  toot unfollow   - unfollow an account")
    print("")
    print("To get help for each command run:")
    print("  toot <command> --help")
    print("")
    print("https://github.com/ihabunek/toot")


def print_timeline(item):
    def wrap_text(text, width):
        wrapper = TextWrapper(width=width, break_long_words=False, break_on_hyphens=False)
        return chain(*[wrapper.wrap(l) for l in text.split("\n")])

    def timeline_rows(item):
        name = item['name']
        time = item['time'].strftime('%Y-%m-%d %H:%M%Z')

        left_column = [name, time]
        if 'reblogged' in item:
            left_column.append(item['reblogged'])

        text = item['text']

        right_column = wrap_text(text, 80)

        return zip_longest(left_column, right_column, fillvalue="")

    for left, right in timeline_rows(item):
        print("{:30} │ {}".format(left.encode("utf-8"), right.encode("utf-8")))


def parse_timeline(item):
    content = item['reblog']['content'] if item['reblog'] else item['content']
    reblogged = item['reblog']['account']['username'] if item['reblog'] else ""

    name = item['account']['display_name'] + " @" + item['account']['username']
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text().replace('&apos;', "'")
    time = datetime.strptime(item['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ")

    return {
        "name": name,
        "text": text,
        "time": time,
        "reblogged": reblogged,
    }


def cmd_timeline(app, user, args):
    parser = ArgumentParser(prog="toot timeline",
                            description="Show recent items in your public timeline",
                            epilog="https://github.com/ihabunek/toot")

    args = parser.parse_args(args)

    items = api.timeline_home(app, user)
    parsed_items = [parse_timeline(t) for t in items]

    print("─" * 31 + "┬" + "─" * 88)
    for item in parsed_items:
        print_timeline(item)
        print("─" * 31 + "┼" + "─" * 88)


def visibility(value):
    if value not in ['public', 'unlisted', 'private', 'direct']:
        raise ValueError("Invalid visibility value")

    return value


def cmd_post_status(app, user, args):
    parser = ArgumentParser(prog="toot post",
                            description="Post a status text to the timeline",
                            epilog="https://github.com/ihabunek/toot")
    parser.add_argument("text", help="The status text to post.")
    parser.add_argument("-m", "--media", type=FileType('rb'),
                        help="path to the media file to attach")
    parser.add_argument("-v", "--visibility", type=visibility, default="public",
                        help='post visibility, either "public" (default), "direct", "private", or "unlisted"')

    args = parser.parse_args(args)

    if args.media:
        media = do_upload(app, user, args.media)
        media_ids = [media['id']]
    else:
        media_ids = None

    response = api.post_status(app, user, args.text, media_ids=media_ids, visibility=args.visibility)

    print("Toot posted: " + green(response.get('url')))


def cmd_auth(app, user, args):
    parser = ArgumentParser(prog="toot auth",
                            description="Show login details",
                            epilog="https://github.com/ihabunek/toot")
    parser.parse_args(args)

    if app and user:
        print("You are logged in to " + green(app.base_url))
        print("Username: " + green(user.username))
        print("App data:  " + green(CONFIG_APP_FILE))
        print("User data: " + green(CONFIG_USER_FILE))
    else:
        print("You are not logged in")


def cmd_login(args):
    parser = ArgumentParser(prog="toot login",
                            description="Log into a Mastodon instance",
                            epilog="https://github.com/ihabunek/toot")
    parser.parse_args(args)

    app = create_app_interactive()
    user = login_interactive(app)

    return app, user


def cmd_logout(app, user, args):
    parser = ArgumentParser(prog="toot logout",
                            description="Log out, delete stored access keys",
                            epilog="https://github.com/ihabunek/toot")
    parser.parse_args(args)

    os.unlink(CONFIG_APP_FILE)
    os.unlink(CONFIG_USER_FILE)
    print("You are now logged out")


def cmd_upload(app, user, args):
    parser = ArgumentParser(prog="toot upload",
                            description="Upload an image or video file",
                            epilog="https://github.com/ihabunek/toot")
    parser.add_argument("file", help="Path to the file to upload", type=FileType('rb'))

    args = parser.parse_args(args)

    response = do_upload(app, user, args.file)

    print("\nSuccessfully uploaded media ID {}, type '{}'".format(
         yellow(response['id']),  yellow(response['type'])))
    print("Original URL: " + green(response['url']))
    print("Preview URL:  " + green(response['preview_url']))
    print("Text URL:     " + green(response['text_url']))


def _print_accounts(accounts):
    if not accounts:
        return

    print("\nAccounts:")
    for account in accounts:
        acct = green("@{}".format(account['acct']))
        display_name = account['display_name']
        print("* {} {}".format(acct, display_name))


def _print_hashtags(hashtags):
    if not hashtags:
        return

    print("\nHashtags:")
    print(", ".join([green("#" + t) for t in hashtags]))


def cmd_search(app, user, args):
    parser = ArgumentParser(prog="toot search",
                            description="Search for content",
                            epilog="https://github.com/ihabunek/toot")

    parser.add_argument("query", help="The search query")
    parser.add_argument("-r", "--resolve", action='store_true', default=False,
                        help="Whether to resolve non-local accounts")

    args = parser.parse_args(args)

    response = api.search(app, user, args.query, args.resolve)

    _print_accounts(response['accounts'])
    _print_hashtags(response['hashtags'])


def do_upload(app, user, file):
    print("Uploading media: {}".format(green(file.name)))
    return api.upload_media(app, user, file)


def _find_account(app, user, account_name):
    """For a given account name, returns the Account object or None if not found."""
    response = api.search(app, user, account_name, False)

    for account in response['accounts']:
        if account['acct'] == account_name:
            return account


def cmd_follow(app, user, args):
    parser = ArgumentParser(prog="toot follow",
                            description="Follow an account",
                            epilog="https://github.com/ihabunek/toot")
    parser.add_argument("account", help="Account name, e.g. 'Gargron' or 'polymerwitch@toot.cat'")
    args = parser.parse_args(args)

    account = _find_account(app, user, args.account)

    if not account:
        print_error("Account not found")
        return

    api.follow(app, user, account['id'])

    print(green(u"✓ You are now following %s" % args.account))


def cmd_unfollow(app, user, args):
    parser = ArgumentParser(prog="toot unfollow",
                            description="Unfollow an account",
                            epilog="https://github.com/ihabunek/toot")
    parser.add_argument("account", help="Account name, e.g. 'Gargron' or 'polymerwitch@toot.cat'")
    args = parser.parse_args(args)

    account = _find_account(app, user, args.account)

    if not account:
        print_error("Account not found")
        return

    api.unfollow(app, user, account['id'])

    print(green(u"✓ You are no longer following %s" % args.account))


def run_command(command, args):
    app = load_app()
    user = load_user()

    # Commands which can run when not logged in
    if command == 'login':
        return cmd_login(args)

    if command == 'auth':
        return cmd_auth(app, user, args)

    # Commands which require user to be logged in
    if not app or not user:
        print_error("You are not logged in.")
        print_error("Please run `toot login` first.")
        return

    if command == 'logout':
        return cmd_logout(app, user, args)

    if command == 'post':
        return cmd_post_status(app, user, args)

    if command == 'timeline':
        return cmd_timeline(app, user, args)

    if command == 'upload':
        return cmd_upload(app, user, args)

    if command == 'search':
        return cmd_search(app, user, args)

    if command == 'follow':
        return cmd_follow(app, user, args)

    if command == 'unfollow':
        return cmd_unfollow(app, user, args)

    print_error("Unknown command '{}'\n".format(command))
    print_usage()


def main():
    if os.getenv('TOOT_DEBUG'):
        logging.basicConfig(level=logging.DEBUG)

    command = sys.argv[1] if len(sys.argv) > 1 else None
    args = sys.argv[2:]

    if not command:
        return print_usage()

    try:
        run_command(command, args)
    except ConsoleError as e:
        print_error(str(e))
    except ApiError as e:
        print_error(str(e))
