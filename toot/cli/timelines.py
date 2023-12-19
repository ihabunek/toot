import sys
import click

from toot import api
from toot.cli import cli, get_context, pass_context, Context
from typing import Optional
from toot.cli.validators import validate_instance

from toot.entities import Notification, Status, from_dict
from toot.output import print_notifications, print_timeline


@cli.command()
@click.option(
    "--instance", "-i",
    callback=validate_instance,
    help="""Domain or base URL of the instance from which to read,
            e.g. 'mastodon.social' or 'https://mastodon.social'""",
)
@click.option("--account", "-a", help="Show account timeline")
@click.option("--list", help="Show list timeline")
@click.option("--tag", "-t", help="Show hashtag timeline")
@click.option("--public", "-p", is_flag=True, help="Show public timeline")
@click.option(
    "--local", "-l", is_flag=True,
    help="Show only statuses from the local instance (public and tag timelines only)"
)
@click.option(
    "--reverse", "-r", is_flag=True,
    help="Reverse the order of the shown timeline (new posts at the bottom)"
)
@click.option(
    "--once", "-1", is_flag=True,
    help="Only show the first <count> toots, do not prompt to continue"
)
@click.option(
    "--count", "-c", type=int, default=10,
    help="Number of posts per page (max 20)"
)
def timeline(
    instance: Optional[str],
    account: Optional[str],
    list: Optional[str],
    tag: Optional[str],
    public: bool,
    local: bool,
    reverse: bool,
    once: bool,
    count: int,
):
    """Show recent items in a timeline

    By default shows the home timeline.
    """
    if len([arg for arg in [tag, list, public, account] if arg]) > 1:
        raise click.ClickException("Only one of --public, --tag, --account, or --list can be used at one time.")

    if local and not (public or tag):
        raise click.ClickException("The --local option is only valid alongside --public or --tag.")

    if instance and not (public or tag):
        raise click.ClickException("The --instance option is only valid alongside --public or --tag.")

    if public and instance:
        generator = api.anon_public_timeline_generator(instance, local, count)
    elif tag and instance:
        generator = api.anon_tag_timeline_generator(instance, tag, local, count)
    else:
        ctx = get_context()
        list_id = _get_list_id(ctx, list)

        """Show recent statuses in a timeline"""
        generator = api.get_timeline_generator(
            ctx.app,
            ctx.user,
            account=account,
            list_id=list_id,
            tag=tag,
            public=public,
            local=local,
            limit=count,
        )

    _show_timeline(generator, reverse, once)


@cli.command()
@click.option(
    "--reverse", "-r", is_flag=True,
    help="Reverse the order of the shown timeline (new posts at the bottom)"
)
@click.option(
    "--once", "-1", is_flag=True,
    help="Only show the first <count> toots, do not prompt to continue"
)
@click.option(
    "--count", "-c", type=int, default=10,
    help="Number of posts per page (max 20)"
)
@pass_context
def bookmarks(
    ctx: Context,
    reverse: bool,
    once: bool,
    count: int,
):
    """Show recent statuses in a timeline"""
    generator = api.bookmark_timeline_generator(ctx.app, ctx.user, limit=count)
    _show_timeline(generator, reverse, once)


@cli.command()
@click.option("--clear", help="Dismiss all notifications and exit")
@click.option(
    "--reverse", "-r", is_flag=True,
    help="Reverse the order of the shown notifications (newest on top)"
)
@click.option(
    "--mentions", "-m", is_flag=True,
    help="Show only mentions"
)
@pass_context
def notifications(
    ctx: Context,
    clear: bool,
    reverse: bool,
    mentions: int,
):
    """Show notifications"""
    if clear:
        api.clear_notifications(ctx.app, ctx.user)
        click.secho("✓ Notifications cleared", fg="green")
        return

    exclude = []
    if mentions:
        # Filter everything except mentions
        # https://docs.joinmastodon.org/methods/notifications/
        exclude = ["follow", "favourite", "reblog", "poll", "follow_request"]

    notifications = api.get_notifications(ctx.app, ctx.user, exclude_types=exclude)

    if not notifications:
        click.echo("You have no notifications")
        return

    if reverse:
        notifications = reversed(notifications)

    notifications = [from_dict(Notification, n) for n in notifications]
    print_notifications(notifications)


def _show_timeline(generator, reverse, once):
    while True:
        try:
            items = next(generator)
        except StopIteration:
            click.echo("That's all folks.")
            return

        if reverse:
            items = reversed(items)

        statuses = [from_dict(Status, item) for item in items]
        print_timeline(statuses)

        if once or not sys.stdout.isatty():
            break

        char = input("\nContinue? [Y/n] ")
        if char.lower() == "n":
            break


def _get_list_id(ctx: Context, value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    lists = api.get_lists(ctx.app, ctx.user)
    for list in lists:
        if list["id"] == value or list["title"] == value:
            return list["id"]
