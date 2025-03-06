import sys
import click

from toot import api
from toot.cli import NOTIFICATION_TYPE_CHOICES, InstanceParamType, cli, get_context, pass_context, Context, json_option
from typing import Optional, Tuple
from toot.cli.validators import validate_instance

from toot.entities import Notification, Status, from_dict
from toot.output import print_notifications, print_timeline, print_warning


@cli.command()
@click.option(
    "--instance", "-i",
    type=InstanceParamType(),
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
    """Show timelines (deprecated, use `toot timelines` instead)

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
@click.option(
    "--clear", is_flag=True,
    help="Dismiss all notifications and exit"
)
@click.option(
    "--reverse", "-r", is_flag=True,
    help="Reverse the order of the shown notifications (newest on top)"
)
@click.option(
    "--type", "-t", "types",
    type=click.Choice(NOTIFICATION_TYPE_CHOICES),
    multiple=True,
    help="Types to include in the result, can be specified multiple times"
)
@click.option(
    "--exclude-type", "-e", "exclude_types",
    type=click.Choice(NOTIFICATION_TYPE_CHOICES),
    multiple=True,
    help="Types to exclude in the result, can be specified multiple times"
)
@click.option(
    "--mentions", "-m", is_flag=True,
    help="Show only mentions (same as --type mention, overrides --type, DEPRECATED)"
)
@json_option
@pass_context
def notifications(
    ctx: Context,
    clear: bool,
    reverse: bool,
    mentions: bool,
    types: Tuple[str],
    exclude_types: Tuple[str],
    json: bool,
):
    """Show notifications"""
    if clear:
        api.clear_notifications(ctx.app, ctx.user)
        click.secho("✓ Notifications cleared", fg="green")
        return

    if mentions:
        print_warning("`--mentions` option is deprecated in favour of `--type mentions`")
        types = ("mention",)

    response = api.get_notifications(ctx.app, ctx.user, types=types, exclude_types=exclude_types)

    if json:
        if reverse:
            print_warning("--reverse is not supported alongside --json, ignoring")
        click.echo(response.text)
        return

    notifications = [from_dict(Notification, n) for n in response.json()]
    if reverse:
        notifications = reversed(notifications)

    if notifications:
        print_notifications(notifications)
    else:
        click.echo("You have no notifications")


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
