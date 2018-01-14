# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from datetime import datetime
from itertools import zip_longest
from itertools import chain
from textwrap import TextWrapper

from toot import api, config
from toot.auth import login_interactive, login_browser_interactive, create_app_interactive
from toot.exceptions import ConsoleError, NotFoundError
from toot.output import print_out, print_err, print_instance, print_account, print_search_results
from toot.utils import assert_domain_exists


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
    from toot.ui.app import TimelineApp

    if not args.public and (not app or not user):
        raise ConsoleError("You must be logged in to view the home timeline.")

    if args.public:
        instance = args.instance or app.instance
        generator = api.public_timeline_generator(instance)
    else:
        generator = api.home_timeline_generator(app, user)

    TimelineApp(generator).run()


def post(app, user, args):
    if args.media:
        media = _do_upload(app, user, args.media)
        media_ids = [media['id']]
    else:
        media = None
        media_ids = None

    if media and not args.text:
        args.text = media['text_url']

    if not args.text:
        raise ConsoleError("You must specify either text or media to post.")

    response = api.post_status(app, user, args.text, args.visibility, media_ids)

    print_out("Toot posted: <green>{}</green>".format(response.get('url')))


def auth(app, user, args):
    config_data = config.load_config()

    if not config_data["users"]:
        print_out("You are not logged in to any accounts")
        return

    active_user = config_data["active_user"]

    print_out("Authenticated accounts:")
    for uid, u in config_data["users"].items():
        active_label = "ACTIVE" if active_user == uid else ""
        print_out("* <green>{}</green> <yellow>{}</yellow>".format(uid, active_label))

    path = config.get_config_file_path()
    print_out("\nAuth tokens are stored in: <blue>{}</blue>".format(path))


def login(app, user, args):
    app = create_app_interactive(instance=args.instance)
    login_interactive(app, args.email)

    print_out()
    print_out("<green>✓ Successfully logged in.</green>")


def login_browser(app, user, args):
    app = create_app_interactive(instance=args.instance)
    login_browser_interactive(app)

    print_out()
    print_out("<green>✓ Successfully logged in.</green>")


def logout(app, user, args):
    user = config.load_user(args.account, throw=True)
    config.delete_user(user)
    print_out("<green>✓ User {} logged out</green>".format(config.user_id(user)))


def activate(app, user, args):
    user = config.load_user(args.account, throw=True)
    config.activate_user(user)
    print_out("<green>✓ User {} active</green>".format(config.user_id(user)))


def upload(app, user, args):
    response = _do_upload(app, user, args.file)

    msg = "Successfully uploaded media ID <yellow>{}</yellow>, type '<yellow>{}</yellow>'"

    print_out()
    print_out(msg.format(response['id'], response['type']))
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

    assert_domain_exists(name)

    try:
        instance = api.get_instance(name)
        print_instance(instance)
    except NotFoundError:
        raise ConsoleError(
            "Instance not found at {}.\n"
            "The given domain probably does not host a Mastodon instance.".format(name)
        )
