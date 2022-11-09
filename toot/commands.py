# -*- coding: utf-8 -*-

import sys

from toot import api, config
from toot.auth import login_interactive, login_browser_interactive, create_app_interactive
from toot.exceptions import ConsoleError, NotFoundError
from toot.output import (print_out, print_instance, print_account,
                         print_search_results, print_timeline, print_notifications)
from toot.utils import assert_domain_exists, parse_editor_input, multiline_input, EOF_KEY


def get_timeline_generator(app, user, args):
    # Make sure tag, list and public are not used simultaneously
    if len([arg for arg in [args.tag, args.list, args.public] if arg]) > 1:
        raise ConsoleError("Only one of --public, --tag, or --list can be used at one time.")

    if args.local and not (args.public or args.tag):
        raise ConsoleError("The --local option is only valid alongside --public or --tag.")

    if args.instance and not (args.public or args.tag):
        raise ConsoleError("The --instance option is only valid alongside --public or --tag.")

    if args.public:
        if args.instance:
            return api.anon_public_timeline_generator(args.instance, local=args.local, limit=args.count)
        else:
            return api.public_timeline_generator(app, user, local=args.local, limit=args.count)
    elif args.tag:
        if args.instance:
            return api.anon_tag_timeline_generator(args.instance, args.tag, limit=args.count)
        else:
            return api.tag_timeline_generator(app, user, args.tag, local=args.local, limit=args.count)
    elif args.list:
        return api.timeline_list_generator(app, user, args.list, limit=args.count)
    else:
        return api.home_timeline_generator(app, user, limit=args.count)


def timeline(app, user, args):
    generator = get_timeline_generator(app, user, args)

    while(True):
        try:
            items = next(generator)
        except StopIteration:
            print_out("That's all folks.")
            return

        if args.reverse:
            items = reversed(items)

        print_timeline(items)

        if args.once or not sys.stdout.isatty():
            break

        char = input("\nContinue? [Y/n] ")
        if char.lower() == "n":
            break


def thread(app, user, args):
    toot = api.single_status(app, user, args.status_id)
    context = api.context(app, user, args.status_id)
    thread = []
    for item in context['ancestors']:
        thread.append(item)

    thread.append(toot)

    for item in context['descendants']:
        thread.append(item)

    print_timeline(thread)


def post(app, user, args):
    if args.editor:
        # TODO: this might be achievable, explore options
        if not sys.stdin.isatty():
            raise ConsoleError("Cannot run editor if not in tty.")
        prev_using = args.using
        args = parse_editor_input(args)
        # The user may have changed the account
        if args.using != prev_using:
            user, app = config.get_user_app(parsed_args.using)
            # no need to check, this was done in parse_editor_input()


    if args.media and len(args.media) > 4:
        raise ConsoleError("Cannot attach more than 4 files.")

    # Read any text that might be piped to stdin
    if not args.text and not sys.stdin.isatty():
        args.text = sys.stdin.read().rstrip()

    # Match media to corresponding description and upload
    media = args.media or []
    descriptions = args.description or []
    uploaded_media = []

    for idx, file in enumerate(media):
        description = descriptions[idx].strip() if idx < len(descriptions) else None
        result = _do_upload(app, user, file, description)
        uploaded_media.append(result)

    media_ids = [m["id"] for m in uploaded_media]

    if uploaded_media and not args.text:
        args.text = "\n".join(m['text_url'] for m in uploaded_media)

    if not args.editor and not args.text:
        print_out("Write or paste your toot. Press <yellow>{}</yellow> to post it.".format(EOF_KEY))
        args.text = multiline_input()

    if not args.text:
        raise ConsoleError("You must specify either text or media to post.")

    response = api.post_status(
        app, user, args.text,
        visibility=args.visibility,
        media_ids=media_ids,
        sensitive=args.sensitive,
        spoiler_text=args.spoiler_text,
        in_reply_to_id=args.reply_to,
        language=args.language,
        scheduled_at=args.scheduled_at,
        content_type=args.content_type
    )

    if "scheduled_at" in response:
        print_out("Toot scheduled for: <green>{}</green>".format(response["scheduled_at"]))
    else:
        print_out("Toot posted: <green>{}</green>".format(response.get('url')))


def delete(app, user, args):
    api.delete_status(app, user, args.status_id)
    print_out("<green>✓ Status deleted</green>")


def favourite(app, user, args):
    api.favourite(app, user, args.status_id)
    print_out("<green>✓ Status favourited</green>")


def unfavourite(app, user, args):
    api.unfavourite(app, user, args.status_id)
    print_out("<green>✓ Status unfavourited</green>")


def reblog(app, user, args):
    api.reblog(app, user, args.status_id)
    print_out("<green>✓ Status reblogged</green>")


def unreblog(app, user, args):
    api.unreblog(app, user, args.status_id)
    print_out("<green>✓ Status unreblogged</green>")


def pin(app, user, args):
    api.pin(app, user, args.status_id)
    print_out("<green>✓ Status pinned</green>")


def unpin(app, user, args):
    api.unpin(app, user, args.status_id)
    print_out("<green>✓ Status unpinned</green>")


def reblogged_by(app, user, args):
    for account in api.reblogged_by(app, user, args.status_id):
        print_out("{}\n @{}".format(account['display_name'], account['acct']))


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


def login_cli(app, user, args):
    app = create_app_interactive(instance=args.instance, scheme=args.scheme)
    login_interactive(app, args.email)

    print_out()
    print_out("<green>✓ Successfully logged in.</green>")


def login(app, user, args):
    app = create_app_interactive(instance=args.instance, scheme=args.scheme)
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
    response = _do_upload(app, user, args.file, args.description)

    msg = "Successfully uploaded media ID <yellow>{}</yellow>, type '<yellow>{}</yellow>'"

    print_out()
    print_out(msg.format(response['id'], response['type']))
    print_out("Original URL: <green>{}</green>".format(response['url']))
    print_out("Preview URL:  <green>{}</green>".format(response['preview_url']))
    print_out("Text URL:     <green>{}</green>".format(response['text_url']))


def search(app, user, args):
    response = api.search(app, user, args.query, args.resolve)
    print_search_results(response)


def _do_upload(app, user, file, description):
    print_out("Uploading media: <green>{}</green>".format(file.name))
    return api.upload_media(app, user, file, description=description)


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
        # Normalise string matching because usernames are case insensitive
        if account['acct'].lower() == account_name.lower():
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
        instance = api.get_instance(name, args.scheme)
        print_instance(instance)
    except NotFoundError:
        raise ConsoleError(
            "Instance not found at {}.\n"
            "The given domain probably does not host a Mastodon instance.".format(name)
        )


def notifications(app, user, args):
    if args.clear:
        api.clear_notifications(app, user)
        print_out("<green>Cleared notifications</green>")
        return

    exclude = []
    if args.mentions:
        # Filter everything except mentions
        # https://docs.joinmastodon.org/methods/notifications/
        exclude = ["follow", "favourite", "reblog", "poll", "follow_request"]
    notifications = api.get_notifications(app, user, exclude_types=exclude)
    if not notifications:
        print_out("<yellow>No notification</yellow>")
        return

    if args.reverse:
        notifications = reversed(notifications)

    print_notifications(notifications)


def tui(app, user, args):
    from .tui.app import TUI
    TUI.create(app, user).run()
