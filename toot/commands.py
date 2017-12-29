# -*- coding: utf-8 -*-

import webbrowser

from bs4 import BeautifulSoup
from builtins import input
from datetime import datetime
from itertools import zip_longest
from getpass import getpass
from itertools import chain
from textwrap import TextWrapper

from toot import api, config, DEFAULT_INSTANCE, User, App, ConsoleError
from toot.output import print_out, print_instance, print_account, print_search_results


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


def create_app_interactive(instance=None):
    if not instance:
        print_out("Choose an instance [<green>{}</green>]: ".format(DEFAULT_INSTANCE), end="")
        instance = input()
        if not instance:
            instance = DEFAULT_INSTANCE

    return config.load_app(instance) or register_app(instance)


def create_user(app, email, access_token):
    user = User(app.instance, email, access_token)
    path = config.save_user(user)

    print_out("Access token saved to: <green>{}</green>".format(path))

    return user


def login_interactive(app, email=None):
    print_out("Log in to <green>{}</green>".format(app.instance))

    if email:
        print_out("Email: <green>{}</green>".format(email))

    while not email:
        email = input('Email: ')

    password = getpass('Password: ')

    try:
        print_out("Authenticating...")
        response = api.login(app, email, password)
    except api.ApiError:
        raise ConsoleError("Login failed")

    return create_user(app, email, response['access_token'])


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
    from toot.app import TimelineApp
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
    app = create_app_interactive(instance=args.instance)
    login_interactive(app, args.email)

    print_out()
    print_out("<green>✓ Successfully logged in.</green>")


BROWSER_LOGIN_EXPLANATION = """
This authentication method requires you to log into your Mastodon instance
in your browser, where you will be asked to authorize <yellow>toot</yellow> to access
your account. When you do, you will be given an <yellow>authorization code</yellow>
which you need to paste here.
"""


def login_browser(app, user, args):
    app = create_app_interactive(instance=args.instance)
    url = api.get_browser_login_url(app)

    print_out(BROWSER_LOGIN_EXPLANATION)

    print_out("This is the login URL:")
    print_out(url)
    print_out("")

    yesno = input("Open link in default browser? [Y/n]")
    if not yesno or yesno.lower() == 'y':
        webbrowser.open(url)

    authorization_code = ""
    while not authorization_code:
        authorization_code = input("Authorization code: ")

    print_out("\nRequesting access token...")
    response = api.request_access_token(app, authorization_code)

    # TODO: user email is not available in this workflow, maybe change the User
    # to store the username instead? Currently set to "unknown" since it's not
    # used anywhere.
    email = "unknown"

    create_user(app, email, response['access_token'])

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


def search(app, user, args):
    response = api.search(app, user, args.query, args.resolve)
    print_search_results(response)


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
    print_account(account)


def whois(app, user, args):
    account = _find_account(app, user, args.account)
    print_account(account)


def instance(app, user, args):
    name = args.instance or (app and app.instance)
    if not name:
        raise ConsoleError("Please specify instance name.")

    instance = api.get_instance(app, user, name)
    print_instance(instance)
