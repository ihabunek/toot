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

from .config import save_user, load_user, load_app, save_app, CONFIG_APP_FILE, CONFIG_USER_FILE
from . import create_app, login, post_status, timeline_home, upload_media, DEFAULT_INSTANCE


class ConsoleError(Exception):
    pass


def red(text):
    return "\033[31m{}\033[0m".format(text)


def green(text):
    return "\033[32m{}\033[0m".format(text)


def yellow(text):
    return "\033[33m{}\033[0m".format(text)


def print_error(text):
    print(red(text), file=sys.stderr)


def create_app_interactive():
    instance = input("Choose an instance [%s]: " % green(DEFAULT_INSTANCE))
    if not instance:
        instance = DEFAULT_INSTANCE

    base_url = 'https://{}'.format(instance)

    print("Registering application with %s" % green(base_url))
    try:
        app = create_app(base_url)
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
        user = login(app, email, password)
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
    print("  toot timeline   - shows your public timeline")
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
        print("{:30} │ {}".format(left, right))


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

    items = timeline_home(app, user)
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

    response = post_status(app, user, args.text, media_ids=media_ids, visibility=args.visibility)

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


def cmd_login():
    parser = ArgumentParser(prog="toot login",
                            description="Log into a Mastodon instance",
                            epilog="https://github.com/ihabunek/toot")
    parser.parse_args()

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


def do_upload(app, user, file):
    print("Uploading media: {}".format(green(file.name)))
    return upload_media(app, user, file)


def run_command(command, args):
    app = load_app()
    user = load_user()

    # Commands which can run when not logged in
    if command == 'login':
        return cmd_login()

    if command == 'auth':
        return cmd_auth(app, user, args)

    # Commands which require user to be logged in
    if not app or not user:
        print(red("You are not logged in."))
        print(red("Please run `toot login` first."))
        return

    if command == 'logout':
        return cmd_logout(app, user, args)

    if command == 'post':
        return cmd_post_status(app, user, args)

    if command == 'timeline':
        return cmd_timeline(app, user, args)

    if command == 'upload':
        return cmd_upload(app, user, args)

    print(red("Unknown command '{}'\n".format(command)))
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
