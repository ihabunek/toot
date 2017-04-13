import os
import sys

from bs4 import BeautifulSoup
from builtins import input
from datetime import datetime
from getpass import getpass
from itertools import chain
from textwrap import TextWrapper
from future.moves.itertools import zip_longest

from .config import save_user, load_user, load_app, save_app, CONFIG_APP_FILE, CONFIG_USER_FILE
from . import create_app, login, post_status, timeline_home, DEFAULT_INSTANCE


def green(text):
    return "\033[92m{}\033[0m".format(text)


def red(text):
    return "\033[91m{}\033[0m".format(text)


def create_app_interactive():
    instance = input("Choose an instance [{}]: ".format(DEFAULT_INSTANCE))
    if not instance:
        instance = DEFAULT_INSTANCE

    base_url = 'https://{}'.format(instance)

    print("Creating app with {}".format(base_url))
    app = create_app(base_url)

    print("App tokens saved to: {}".format(green(CONFIG_APP_FILE)))
    save_app(app)

    return app


def login_interactive(app):
    print("\nLog in to " + green(app.base_url))
    email = input('Email: ')
    password = getpass('Password: ')

    print("Authenticating...")
    user = login(app, email, password)

    save_user(user)
    print("User token saved to " + green(CONFIG_USER_FILE))

    return user


def print_usage():
    print("toot - interact with Mastodon from the command line")
    print("")
    print("Usage:")
    print("    toot post \"All your base are belong to us\"")
    print("    toot timeline")
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
        # "username": item['account']['username'],
        "name": name,
        "text": text,
        "time": time,
        "reblogged": reblogged,
    }


def cmd_timeline(app, user):
    items = timeline_home(app, user)
    parsed_items = [parse_timeline(t) for t in items]

    print("─" * 31 + "┬" + "─" * 88)
    for item in parsed_items:
        print_timeline(item)
        print("─" * 31 + "┼" + "─" * 88)


def cmd_post_status(app, user):
    if len(sys.argv) < 3:
        print(red("No status text given"))
        return

    response = post_status(app, user, sys.argv[2])

    print("Toot posted: " + green(response.get('url')))


def cmd_auth(app, user):
    if app and user:
        print("You are logged in to " + green(app.base_url))
        print("Username: " + green(user.username))
        print("App data:  " + green(CONFIG_APP_FILE))
        print("User data: " + green(CONFIG_USER_FILE))
    else:
        print("You are not logged in")


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else None

    if os.getenv('TOOT_DEBUG'):
        import logging
        logging.basicConfig(level=logging.DEBUG)

    app = load_app() or create_app_interactive()
    user = load_user() or login_interactive(app)

    if command == 'post':
        cmd_post_status(app, user)
    elif command == 'auth':
        cmd_auth(app, user)
    elif command == 'timeline':
        cmd_timeline(app, user)
    else:
        print_usage()
