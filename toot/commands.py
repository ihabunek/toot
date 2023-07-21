
import sys
import platform

from datetime import datetime, timedelta, timezone
from time import sleep, time
from toot import api, config, __version__
from toot.auth import login_interactive, login_browser_interactive, create_app_interactive
from toot.entities import Instance, Notification, Status, from_dict
from toot.exceptions import ApiError, ConsoleError
from toot.output import (print_lists, print_out, print_instance, print_account, print_acct_list,
                         print_search_results, print_status, print_timeline, print_notifications, print_tag_list,
                         print_list_accounts, print_user_list)
from toot.utils import args_get_instance, delete_tmp_status_file, editor_input, multiline_input, EOF_KEY
from toot.utils.datetime import parse_datetime


def get_timeline_generator(app, user, args):
    if len([arg for arg in [args.tag, args.list, args.public, args.account] if arg]) > 1:
        raise ConsoleError("Only one of --public, --tag, --account, or --list can be used at one time.")

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
    elif args.account:
        return api.account_timeline_generator(app, user, args.account, limit=args.count)
    elif args.list:
        return api.timeline_list_generator(app, user, args.list, limit=args.count)
    else:
        return api.home_timeline_generator(app, user, limit=args.count)


def timeline(app, user, args, generator=None):
    if not generator:
        generator = get_timeline_generator(app, user, args)

    while True:
        try:
            items = next(generator)
        except StopIteration:
            print_out("That's all folks.")
            return

        if args.reverse:
            items = reversed(items)

        statuses = [from_dict(Status, item) for item in items]
        print_timeline(statuses)

        if args.once or not sys.stdout.isatty():
            break

        char = input("\nContinue? [Y/n] ")
        if char.lower() == "n":
            break


def status(app, user, args):
    status = api.single_status(app, user, args.status_id)
    status = from_dict(Status, status)
    print_status(status)


def thread(app, user, args):
    toot = api.single_status(app, user, args.status_id)
    context = api.context(app, user, args.status_id)
    thread = []
    for item in context['ancestors']:
        thread.append(item)

    thread.append(toot)

    for item in context['descendants']:
        thread.append(item)

    statuses = [from_dict(Status, s) for s in thread]
    print_timeline(statuses)


def post(app, user, args):
    if args.editor and not sys.stdin.isatty():
        raise ConsoleError("Cannot run editor if not in tty.")

    if args.media and len(args.media) > 4:
        raise ConsoleError("Cannot attach more than 4 files.")

    media_ids = _upload_media(app, user, args)
    status_text = _get_status_text(args.text, args.editor, args.media)
    scheduled_at = _get_scheduled_at(args.scheduled_at, args.scheduled_in)

    if not status_text and not media_ids:
        raise ConsoleError("You must specify either text or media to post.")

    response = api.post_status(
        app, user, status_text,
        visibility=args.visibility,
        media_ids=media_ids,
        sensitive=args.sensitive,
        spoiler_text=args.spoiler_text,
        in_reply_to_id=args.reply_to,
        language=args.language,
        scheduled_at=scheduled_at,
        content_type=args.content_type,
        poll_options=args.poll_option,
        poll_expires_in=args.poll_expires_in,
        poll_multiple=args.poll_multiple,
        poll_hide_totals=args.poll_hide_totals,
    )

    if "scheduled_at" in response:
        scheduled_at = parse_datetime(response["scheduled_at"])
        scheduled_at = datetime.strftime(scheduled_at, "%Y-%m-%d %H:%M:%S%z")
        print_out(f"Toot scheduled for: <green>{scheduled_at}</green>")
    else:
        print_out(f"Toot posted: <green>{response['url']}")

    delete_tmp_status_file()


def _get_status_text(text, editor, media):
    isatty = sys.stdin.isatty()

    if not text and not isatty:
        text = sys.stdin.read().rstrip()

    if isatty:
        if editor:
            text = editor_input(editor, text)
        elif not text and not media:
            print_out("Write or paste your toot. Press <yellow>{}</yellow> to post it.".format(EOF_KEY))
            text = multiline_input()

    return text


def _get_scheduled_at(scheduled_at, scheduled_in):
    if scheduled_at:
        return scheduled_at

    if scheduled_in:
        scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=scheduled_in)
        return scheduled_at.replace(microsecond=0).isoformat()

    return None


def _upload_media(app, user, args):
    # Match media to corresponding description and thumbnail
    media = args.media or []
    descriptions = args.description or []
    thumbnails = args.thumbnail or []
    uploaded_media = []

    for idx, file in enumerate(media):
        description = descriptions[idx].strip() if idx < len(descriptions) else None
        thumbnail = thumbnails[idx] if idx < len(thumbnails) else None
        result = _do_upload(app, user, file, description, thumbnail)
        uploaded_media.append(result)

    _wait_until_all_processed(app, user, uploaded_media)

    return [m["id"] for m in uploaded_media]


def _wait_until_all_processed(app, user, uploaded_media):
    """
    Media is uploaded asynchronously, and cannot be attached until the server
    has finished processing it. This function waits for that to happen.

    Once media is processed, it will have the URL populated.
    """
    if all(m["url"] for m in uploaded_media):
        return

    # Timeout after waiting 1 minute
    start_time = time()
    timeout = 60

    print_out("<dim>Waiting for media to finish processing...</dim>")
    for media in uploaded_media:
        _wait_until_processed(app, user, media, start_time, timeout)


def _wait_until_processed(app, user, media, start_time, timeout):
    if media["url"]:
        return

    media = api.get_media(app, user, media["id"])
    while not media["url"]:
        sleep(1)
        if time() > start_time + timeout:
            raise ConsoleError(f"Media not processed by server after {timeout} seconds. Aborting.")
        media = api.get_media(app, user, media["id"])


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
    api.reblog(app, user, args.status_id, visibility=args.visibility)
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


def bookmark(app, user, args):
    api.bookmark(app, user, args.status_id)
    print_out("<green>✓ Status bookmarked</green>")


def unbookmark(app, user, args):
    api.unbookmark(app, user, args.status_id)
    print_out("<green>✓ Status unbookmarked</green>")


def bookmarks(app, user, args):
    timeline(app, user, args, api.bookmark_timeline_generator(app, user, limit=args.count))


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


def env(app, user, args):
    print_out(f"toot {__version__}")
    print_out(f"Python {sys.version}")
    print_out(platform.platform())


def update_account(app, user, args):
    options = [
        args.avatar,
        args.bot,
        args.discoverable,
        args.display_name,
        args.header,
        args.language,
        args.locked,
        args.note,
        args.privacy,
        args.sensitive,
    ]

    if all(option is None for option in options):
        raise ConsoleError("Please specify at least one option to update the account")

    api.update_account(
        app,
        user,
        avatar=args.avatar,
        bot=args.bot,
        discoverable=args.discoverable,
        display_name=args.display_name,
        header=args.header,
        language=args.language,
        locked=args.locked,
        note=args.note,
        privacy=args.privacy,
        sensitive=args.sensitive,
    )

    print_out("<green>✓ Account updated</green>")


def login_cli(app, user, args):
    base_url = args_get_instance(args.instance, args.scheme)
    app = create_app_interactive(base_url)
    login_interactive(app, args.email)

    print_out()
    print_out("<green>✓ Successfully logged in.</green>")


def login(app, user, args):
    base_url = args_get_instance(args.instance, args.scheme)
    app = create_app_interactive(base_url)
    login_browser_interactive(app)

    print_out()
    print_out("<green>✓ Successfully logged in.</green>")


def logout(app, user, args):
    user = config.load_user(args.account, throw=True)
    config.delete_user(user)
    print_out("<green>✓ User {} logged out</green>".format(config.user_id(user)))


def activate(app, user, args):
    if not args.account:
        print_out("Specify one of the following user accounts to activate:\n")
        print_user_list(config.get_user_list())
        return

    user = config.load_user(args.account, throw=True)
    config.activate_user(user)
    print_out("<green>✓ User {} active</green>".format(config.user_id(user)))


def upload(app, user, args):
    response = _do_upload(app, user, args.file, args.description, None)

    msg = "Successfully uploaded media ID <yellow>{}</yellow>, type '<yellow>{}</yellow>'"

    print_out()
    print_out(msg.format(response['id'], response['type']))
    print_out("URL: <green>{}</green>".format(response['url']))
    print_out("Preview URL:  <green>{}</green>".format(response['preview_url']))


def search(app, user, args):
    response = api.search(app, user, args.query, args.resolve)
    print_search_results(response)


def _do_upload(app, user, file, description, thumbnail):
    print_out("Uploading media: <green>{}</green>".format(file.name))
    return api.upload_media(app, user, file, description=description, thumbnail=thumbnail)


def follow(app, user, args):
    account = api.find_account(app, user, args.account)
    api.follow(app, user, account['id'])
    print_out("<green>✓ You are now following {}</green>".format(args.account))


def unfollow(app, user, args):
    account = api.find_account(app, user, args.account)
    api.unfollow(app, user, account['id'])
    print_out("<green>✓ You are no longer following {}</green>".format(args.account))


def following(app, user, args):
    account = api.find_account(app, user, args.account)
    response = api.following(app, user, account['id'])
    print_acct_list(response)


def followers(app, user, args):
    account = api.find_account(app, user, args.account)
    response = api.followers(app, user, account['id'])
    print_acct_list(response)


def tags_follow(app, user, args):
    tn = args.tag_name if not args.tag_name.startswith("#") else args.tag_name[1:]
    api.follow_tag(app, user, tn)
    print_out("<green>✓ You are now following #{}</green>".format(tn))


def tags_unfollow(app, user, args):
    tn = args.tag_name if not args.tag_name.startswith("#") else args.tag_name[1:]
    api.unfollow_tag(app, user, tn)
    print_out("<green>✓ You are no longer following #{}</green>".format(tn))


def tags_followed(app, user, args):
    response = api.followed_tags(app, user)
    print_tag_list(response)


def lists(app, user, args):
    lists = api.get_lists(app, user)

    if lists:
        print_lists(lists)
    else:
        print_out("You have no lists defined.")


def list_accounts(app, user, args):
    list_id = _get_list_id(app, user, args)
    response = api.get_list_accounts(app, user, list_id)
    print_list_accounts(response)


def list_create(app, user, args):
    api.create_list(app, user, title=args.title, replies_policy=args.replies_policy)
    print_out(f"<green>✓ List \"{args.title}\" created.</green>")


def list_delete(app, user, args):
    list_id = _get_list_id(app, user, args)
    api.delete_list(app, user, list_id)
    print_out(f"<green>✓ List \"{args.title if args.title else args.id}\"</green> <red>deleted.</red>")


def list_add(app, user, args):
    list_id = _get_list_id(app, user, args)
    account = api.find_account(app, user, args.account)

    try:
        api.add_accounts_to_list(app, user, list_id, [account['id']])
    except Exception as ex:
        # if we failed to add the account, try to give a
        # more specific error message than "record not found"
        my_accounts = api.followers(app, user, account['id'])
        found = False
        if my_accounts:
            for my_account in my_accounts:
                if my_account['id'] == account['id']:
                    found = True
                    break
        if found is False:
            print_out(f"<red>You must follow @{account['acct']} before adding this account to a list.</red>")
        else:
            print_out(f"<red>{ex}</red>")
        return

    print_out(f"<green>✓ Added account \"{args.account}\"</green>")


def list_remove(app, user, args):
    list_id = _get_list_id(app, user, args)
    account = api.find_account(app, user, args.account)
    api.remove_accounts_from_list(app, user, list_id, [account['id']])
    print_out(f"<green>✓ Removed account \"{args.account}\"</green>")


def _get_list_id(app, user, args):
    list_id = args.id or api.find_list_id(app, user, args.title)
    if not list_id:
        raise ConsoleError("List not found")
    return list_id


def mute(app, user, args):
    account = api.find_account(app, user, args.account)
    api.mute(app, user, account['id'])
    print_out("<green>✓ You have muted {}</green>".format(args.account))


def unmute(app, user, args):
    account = api.find_account(app, user, args.account)
    api.unmute(app, user, account['id'])
    print_out("<green>✓ {} is no longer muted</green>".format(args.account))


def muted(app, user, args):
    response = api.muted(app, user)
    print_acct_list(response)


def block(app, user, args):
    account = api.find_account(app, user, args.account)
    api.block(app, user, account['id'])
    print_out("<green>✓ You are now blocking {}</green>".format(args.account))


def unblock(app, user, args):
    account = api.find_account(app, user, args.account)
    api.unblock(app, user, account['id'])
    print_out("<green>✓ {} is no longer blocked</green>".format(args.account))


def blocked(app, user, args):
    response = api.blocked(app, user)
    print_acct_list(response)


def whoami(app, user, args):
    account = api.verify_credentials(app, user)
    print_account(account)


def whois(app, user, args):
    account = api.find_account(app, user, args.account)
    print_account(account)


def instance(app, user, args):
    default = app.base_url if app else None
    base_url = args_get_instance(args.instance, args.scheme, default)

    if not base_url:
        raise ConsoleError("Please specify an instance.")

    try:
        instance = api.get_instance(base_url)
        instance = from_dict(Instance, instance)
        print_instance(instance)
    except ApiError:
        raise ConsoleError(
            f"Instance not found at {base_url}.\n"
            "The given domain probably does not host a Mastodon instance."
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

    notifications = [from_dict(Notification, n) for n in notifications]
    print_notifications(notifications)


def tui(app, user, args):
    from .tui.app import TUI
    TUI.create(app, user, args).run()
