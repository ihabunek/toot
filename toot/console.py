import os
import sys

from builtins import input
from getpass import getpass

from .config import save_user, load_user, load_app, save_app, CONFIG_APP_FILE, CONFIG_USER_FILE
from . import create_app, login, post_status, DEFAULT_INSTANCE


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
    print("")
    print("https://github.com/ihabunek/toot")


def cmd_post_status(app, user):
    if len(sys.argv) < 3:
        print(red("No status text given"))
        return

    response = post_status(app, user, sys.argv[2])

    print("Toot posted: " + green(response.get('url')))


def cmd_auth(app, user):
    if app and user:
        print("You are logged in")
        print("Mastodon instance: " + green(app.base_url))
        print("Username: " + green(user.username))
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
    else:
        print_usage()
