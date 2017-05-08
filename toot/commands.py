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
from toot.output import print_out
from toot.app import TimelineApp


def register_app(instance):
    print_out("Registering application with <green>{}</green>".format(instance))

    try:
        response = api.create_app(instance)
    except:
        raise ConsoleError("Registration failed. Did you enter a valid instance?")

    base_url = 'https://' + instance

    app = App(instance, base_url, response['client_id'], response['client_secret'])
    path = config.save_app(app)
    print_out("Application tokens saved to: <green>{}</green>\n".format(path))

    return app


def create_app_interactive():
    print_out("Choose an instance [<green>{}</green>]: ".format(DEFAULT_INSTANCE), end="")

    instance = input()
    if not instance:
        instance = DEFAULT_INSTANCE

    return config.load_app(instance) or register_app(instance)


def login_interactive(app):
    print_out("\nLog in to <green>{}</green>".format(app.instance))

    email = input('Email: ')
    password = getpass('Password: ')

    if not email or not password:
        raise ConsoleError("Email and password cannot be empty.")

    try:
        print_out("Authenticating...")
        response = api.login(app, email, password)
    except api.ApiError:
        raise ConsoleError("Login failed")

    user = User(app.instance, email, response['access_token'])
    path = config.save_user(user)

    print_out("Access token saved to: <green>{}</green>".format(path))

    return user


def two_factor_login_interactive(app):
    """Hacky implementation of two factor authentication"""

    print_out("Log in to {}".format(app.instance))
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
    print_out("Access token saved to: <green>{}</green>".format(path))


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
        print_out("{:30} │ {}".format(left, right))


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

    print_out("─" * 31 + "┬" + "─" * 88)
    for item in parsed_items:
        _print_timeline(item)
        print_out("─" * 31 + "┼" + "─" * 88)


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

    print_out("Toot posted: <green>{}</green>".format(response.get('url')))


def auth(app, user, args):
    if app and user:
        print_out("You are logged in to <yellow>{}</yellow> as <yellow>{}</yellow>\n".format(
            app.instance, user.username))
        print_out("User data: <green>{}</green>".format(config.get_user_config_path()))
        print_out("App data:  <green>{}</green>".format(config.get_instance_config_path(app.instance)))
    else:
        print_out("You are not logged in")


def login(app, user, args):
    app = create_app_interactive()
    login_interactive(app)

    print_out()
    print_out("<green>✓ Successfully logged in.</green>")


def login_2fa(app, user, args):
    print_out()
    print_out("<yellow>Two factor authentication is experimental.</yellow>")
    print_out("<yellow>If you have problems logging in, please open an issue:</yellow>")
    print_out("<yellow>https://github.com/ihabunek/toot/issues</yellow>")
    print_out()

    app = create_app_interactive()
    two_factor_login_interactive(app)

    print_out()
    print_out("<green>✓ Successfully logged in.</green>")


def logout(app, user, args):
    config.delete_user()

    print_out("<green>✓ You are now logged out.</green>")


def upload(app, user, args):
    response = _do_upload(app, user, args.file)

    print_out()
    print_out("Successfully uploaded media ID <yellow>{}</yellow>, type '<yellow>{}</yellow>'".format(
         response['id'],  response['type']))
    print_out("Original URL: <green>{}</green>".format(response['url']))
    print_out("Preview URL:  <green>{}</green>".format(response['preview_url']))
    print_out("Text URL:     <green>{}</green>".format(response['text_url']))


def _print_accounts(accounts):
    if not accounts:
        return

    print_out("\nAccounts:")
    for account in accounts:
        print_out("* <green>@{}</green> {}".format(
            account['acct'],
            account['display_name']
        ))


def _print_hashtags(hashtags):
    if not hashtags:
        return

    print_out("\nHashtags:")
    print_out(", ".join(["<green>#{}</green>".format(t) for t in hashtags]))


def search(app, user, args):
    response = api.search(app, user, args.query, args.resolve)

    _print_accounts(response['accounts'])
    _print_hashtags(response['hashtags'])


def _do_upload(app, user, file):
    print_out("Uploading media: <green>{}</green>".format(file.name))
    return api.upload_media(app, user, file)


def _find_account(app, user, account_name):
    """For a given account name, returns the Account object.

    Raises an exception if not found.
    """
    if not account_name:
        raise ConsoleError("Empty account name given")

    accounts = api.search_accounts(app, user, account_name)

    if account_name[0] == "@":
        account_name = account_name[1:]

    for account in accounts:
        if account['acct'] == account_name:
            return account

    raise ConsoleError("Account not found")


def _print_account(account):
    print_out("<green>@{}</green> {}".format(account['acct'], account['display_name']))

    note = BeautifulSoup(account['note'], "html.parser").get_text()

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


def follow(app, user, args):
    account = _find_account(app, user, args.account)
    api.follow(app, user, account['id'])
    print_out("<green>✓ You are now following {}</green>".format(args.account))


def unfollow(app, user, args):
    account = _find_account(app, user, args.account)
    api.unfollow(app, user, account['id'])
    print_out("<green>✓ You are no longer following {}</green>".format(args.account))


def mute(app, user, args):
    account = _find_account(app, user, args.account)
    api.mute(app, user, account['id'])
    print_out("<green>✓ You have muted {}</green>".format(args.account))


def unmute(app, user, args):
    account = _find_account(app, user, args.account)
    api.unmute(app, user, account['id'])
    print_out("<green>✓ {} is no longer muted</green>".format(args.account))


def block(app, user, args):
    account = _find_account(app, user, args.account)
    api.block(app, user, account['id'])
    print_out("<green>✓ You are now blocking {}</green>".format(args.account))


def unblock(app, user, args):
    account = _find_account(app, user, args.account)
    api.unblock(app, user, account['id'])
    print_out("<green>✓ {} is no longer blocked</green>".format(args.account))


def whoami(app, user, args):
    account = api.verify_credentials(app, user)
    _print_account(account)


def whois(app, user, args):
    account = _find_account(app, user, args.account)
    _print_account(account)
