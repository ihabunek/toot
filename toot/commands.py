# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import json
import requests

from bs4 import BeautifulSoup
from builtins import input
from datetime import datetime
from future.moves.itertools import zip_longest
from getpass import getpass
from itertools import chain
from textwrap import TextWrapper, wrap

from toot import api, config, DEFAULT_INSTANCE, User, App, ConsoleError
from toot.output import green, yellow, print_error
from toot.app import TimelineApp


def register_app(instance):
    print("Registering application with %s" % green(instance))

    try:
        response = api.create_app(instance)
    except:
        raise ConsoleError("Registration failed. Did you enter a valid instance?")

    base_url = 'https://' + instance

    app = App(instance, base_url, response['client_id'], response['client_secret'])
    path = config.save_app(app)
    print("Application tokens saved to: {}\n".format(green(path)))

    return app


def create_app_interactive():
    instance = input("Choose an instance [%s]: " % green(DEFAULT_INSTANCE))
    if not instance:
        instance = DEFAULT_INSTANCE

    return config.load_app(instance) or register_app(instance)


def login_interactive(app):
    print("\nLog in to " + green(app.instance))
    email = input('Email: ')
    password = getpass('Password: ')

    if not email or not password:
        raise ConsoleError("Email and password cannot be empty.")

    try:
        print("Authenticating...")
        response = api.login(app, email, password)
    except api.ApiError:
        raise ConsoleError("Login failed")

    user = User(app.instance, email, response['access_token'])
    path = config.save_user(user)
    print("Access token saved to: " + green(path))

    return user


def two_factor_login_interactive(app):
    """Hacky implementation of two factor authentication"""

    print("Log in to " + green(app.instance))
    email = input('Email: ')
    password = getpass('Password: ')

    sign_in_url = app.base_url + '/auth/sign_in'

    session = requests.Session()

    # Fetch sign in form
    response = session.get(sign_in_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")
    form = soup.find('form')
    inputs = form.find_all('input')

    data = {i.attrs.get('name'): i.attrs.get('value') for i in inputs}
    data['user[email]'] = email
    data['user[password]'] = password

    # Submit form, get 2FA entry form
    response = session.post(sign_in_url, data)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")
    form = soup.find('form')
    inputs = form.find_all('input')

    data = {i.attrs.get('name'): i.attrs.get('value') for i in inputs}
    data['user[otp_attempt]'] = input("2FA Token: ")

    # Submit token
    response = session.post(sign_in_url, data)
    response.raise_for_status()

    # Extract access token from response
    soup = BeautifulSoup(response.content, "html.parser")
    initial_state = soup.find('script', id='initial-state')

    if not initial_state:
        raise ConsoleError("Login failed: Invalid 2FA token?")

    data = json.loads(initial_state.get_text())
    access_token = data['meta']['access_token']

    user = User(app.instance, email, access_token)
    path = config.save_user(user)
    print("Access token saved to: " + green(path))


def _print_timeline(item):
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


def _parse_timeline(item):
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


def timeline(app, user, args):
    items = api.timeline_home(app, user)
    parsed_items = [_parse_timeline(t) for t in items]

    print("─" * 31 + "┬" + "─" * 88)
    for item in parsed_items:
        _print_timeline(item)
        print("─" * 31 + "┼" + "─" * 88)


def curses(app, user, args):
    generator = api.timeline_generator(app, user)
    TimelineApp(generator).run()


def post(app, user, args):
    if args.media:
        media = _do_upload(app, user, args.media)
        media_ids = [media['id']]
    else:
        media_ids = None

    response = api.post_status(app, user, args.text, media_ids=media_ids, visibility=args.visibility)

    print("Toot posted: " + green(response.get('url')))


def auth(app, user, args):
    if app and user:
        print("You are logged in to {} as {}\n".format(
            yellow(app.instance),
            yellow(user.username)
        ))
        print("User data: " + green(config.get_user_config_path()))
        print("App data:  " + green(config.get_instance_config_path(app.instance)))
    else:
        print("You are not logged in")


def login(app, user, args):
    app = create_app_interactive()
    login_interactive(app)

    print()
    print(green("✓ Successfully logged in."))


def login_2fa(app, user, args):
    print()
    print(yellow("Two factor authentication is experimental."))
    print(yellow("If you have problems logging in, please open an issue:"))
    print(yellow("https://github.com/ihabunek/toot/issues"))
    print()

    app = create_app_interactive()
    two_factor_login_interactive(app)

    print()
    print(green("✓ Successfully logged in."))


def logout(app, user, args):
    config.delete_user()

    print(green("✓ You are now logged out"))


def upload(app, user, args):
    response = _do_upload(app, user, args.file)

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


def search(app, user, args):
    response = api.search(app, user, args.query, args.resolve)

    _print_accounts(response['accounts'])
    _print_hashtags(response['hashtags'])


def _do_upload(app, user, file):
    print("Uploading media: {}".format(green(file.name)))
    return api.upload_media(app, user, file)


def _find_account(app, user, account_name):
    """For a given account name, returns the Account object or raises an exception if not found."""
    response = api.search(app, user, account_name, False)

    for account in response['accounts']:
        if account['acct'] == account_name or "@" + account['acct'] == account_name:
            return account

    raise ConsoleError("Account not found")


def _print_account(account):
    print("{} {}".format(green("@" + account['acct']), account['display_name']))

    if account['note']:
        print("")
        note = BeautifulSoup(account['note'], "html.parser")
        print("\n".join(wrap(note.get_text())))

    print("")
    print("ID: " + green(account['id']))
    print("Since: " + green(account['created_at'][:19].replace('T', ' @ ')))
    print("")
    print("Followers: " + yellow(account['followers_count']))
    print("Following: " + yellow(account['following_count']))
    print("Statuses: " + yellow(account['statuses_count']))
    print("")
    print(account['url'])


def follow(app, user, args):
    account = _find_account(app, user, args.account)
    api.follow(app, user, account['id'])
    print(green("✓ You are now following %s" % args.account))


def unfollow(app, user, args):
    account = _find_account(app, user, args.account)
    api.unfollow(app, user, account['id'])
    print(green("✓ You are no longer following %s" % args.account))


def mute(app, user, args):
    account = _find_account(app, user, args.account)
    api.mute(app, user, account['id'])
    print(green("✓ You have muted %s" % args.account))


def unmute(app, user, args):
    account = _find_account(app, user, args.account)
    api.unmute(app, user, account['id'])
    print(green("✓ %s is no longer muted" % args.account))


def block(app, user, args):
    account = _find_account(app, user, args.account)
    api.block(app, user, account['id'])
    print(green("✓ You are now blocking %s" % args.account))


def unblock(app, user, args):
    account = _find_account(app, user, args.account)
    api.unblock(app, user, account['id'])
    print(green("✓ %s is no longer blocked" % args.account))


def whoami(app, user, args):
    account = api.verify_credentials(app, user)
    _print_account(account)


def whois(app, user, args):
    account = _find_account(app, user, args.account)
    _print_account(account)
