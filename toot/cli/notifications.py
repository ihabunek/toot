import json as pyjson
from typing import Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import click
from requests import Response

from toot import api, config
from toot.cli import NOTIFICATION_TYPE_CHOICES, Context, cli, json_option, pass_context
from toot.entities import Notification, NotificationPolicy, from_dict, from_dict_list
from toot.output import print_notification, print_notifications, print_warning
from toot.output import green, red, yellow
from toot.utils import drop_empty_values


POLICY_CHOICE = click.Choice(["accept", "filter", "drop"])


@cli.group(invoke_without_command=True)
@click.option("--clear", is_flag=True, help="Dismiss all notifications and exit")
@click.option(
    "--reverse",
    "-r",
    is_flag=True,
    help="Reverse the order of the shown notifications (newest on top)",
)
@click.option(
    "--type",
    "-t",
    "types",
    type=click.Choice(NOTIFICATION_TYPE_CHOICES),
    multiple=True,
    help="Types to include in the result, can be specified multiple times",
)
@click.option(
    "--exclude-type",
    "-e",
    "exclude_types",
    type=click.Choice(NOTIFICATION_TYPE_CHOICES),
    multiple=True,
    help="Types to exclude in the result, can be specified multiple times",
)
@click.option(
    "--mentions",
    "-m",
    is_flag=True,
    help="Show only mentions (same as --type mention, overrides --type)",
)
@click.pass_context
@json_option
def notifications(
    ctx: click.Context,
    clear: bool,
    reverse: bool,
    mentions: bool,
    types: Tuple[str],
    exclude_types: Tuple[str],
    json: bool,
):
    """Display and manage notifications

    DEPRECATION NOTICE: Running `toot notifications` to list notifications is
    deprecated in favour of `toot notifications list` and will be removed in a
    future version of toot.
    """
    if ctx.invoked_subcommand is None:
        print_warning(
            "`toot notifications` is deprecated in favour of `toot notifications list`.\n"
            + "Run `toot notifications -h` to see other notification-related commands."
        )

        user, app = config.get_active_user_app()
        if not user or not app:
            raise click.ClickException("This command requires you to be logged in.")

        if clear:
            api.clear_notifications(app, user)
            click.secho("✓ Notifications cleared", fg="green")
            return

        if mentions:
            types = ("mention",)

        response = api.get_notifications(
            app, user, types=types, exclude_types=exclude_types
        )

        if json:
            if reverse:
                print_warning("--reverse is not supported alongside --json, ignoring")
            click.echo(response.text)
            return

        notifications = from_dict_list(Notification, response.json())
        if reverse:
            notifications = reversed(notifications)

        if notifications:
            print_notifications(notifications)
        else:
            click.echo("You have no notifications")


@notifications.command()
@click.argument("notification_id")
@json_option
@pass_context
def get(ctx: Context, notification_id: str, json: bool):
    """Show a single notification"""
    response = api.get_notification(ctx.app, ctx.user, notification_id)

    if json:
        click.echo(response.text)
        return

    notification = from_dict(Notification, response.json())
    print_notification(notification)


@notifications.command()
@click.option(
    "--reverse",
    "-r",
    is_flag=True,
    help="Reverse the order of the shown notifications (newest on top)",
)
@click.option(
    "--type",
    "-t",
    "types",
    type=click.Choice(NOTIFICATION_TYPE_CHOICES),
    multiple=True,
    help="Types to include in the result, can be specified multiple times",
)
@click.option(
    "--exclude-type",
    "-e",
    "exclude_types",
    type=click.Choice(NOTIFICATION_TYPE_CHOICES),
    multiple=True,
    help="Types to exclude in the result, can be specified multiple times",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=10,
    help="Number of items per page (max 20)",
)
@click.option(
    "--pager",
    "-p",
    is_flag=True,
    help="Offer to print next page of notifications",
)
@click.option("--max-id", help="All results returned will be lesser than this ID.")
@click.option("--min-id", help="All results returned will be greater than this ID.")
@click.option("--since-id", help="All results returned will be newer than this ID.")
@json_option
@pass_context
def list(
    ctx: Context,
    reverse: bool,
    types: Tuple[str],
    exclude_types: Tuple[str],
    pager: bool,
    limit: int,
    max_id: str,
    min_id: str,
    since_id: str,
    json: bool,
):
    """Show notifications"""
    response = api.get_notifications(
        ctx.app,
        ctx.user,
        types=types,
        exclude_types=exclude_types,
        limit=limit,
        max_id=max_id,
        min_id=min_id,
        since_id=since_id,
    )
    if json:
        if reverse:
            print_warning("--reverse is not supported alongside --json, ignoring")

        if pager:
            print_warning("--pager is not supported alongside --json, ignoring")

        click.echo(response.text)
        return

    notifications = from_dict_list(Notification, response.json())
    if reverse:
        notifications = reversed(notifications)

    if notifications:
        print_notifications(notifications)
        next_url = api._get_next_url(response.headers)

        if pager:
            print(next_url)
            print(next_url)
            print(next_url)
            print(next_url)
        else:
            click.secho("There are more notifications, use --pager to iterate", dim=True)

    else:
        click.echo("You have no notifications")


def _get_paging_params(response: Response, link_name: str) -> Optional[Dict[str, str]]:
    link = response.links.get(link_name)
    if link:
        query = parse_qs(urlparse(link["url"]).query)
        params = {}
        for field in ["max_id", "min_id", "since_id"]:
            if field in query:
                params[field] = query[field][0]
        return params


@notifications.command()
@pass_context
def clear(ctx: Context):
    """Dismiss all notifications"""
    api.clear_notifications(ctx.app, ctx.user)
    click.echo("Notifications cleared")


@notifications.command()
@click.argument("notification_id")
@pass_context
def dismiss(ctx: Context, notification_id: str):
    """Dismiss a notification"""
    api.dismiss_notification(ctx.app, ctx.user, notification_id)
    click.echo("Notification dismissed")


@notifications.command()
@pass_context
@json_option
def unread_count(ctx: Context, json: bool):
    """Get the number of unread notifications"""
    response = api.get_notifications_unread_count(ctx.app, ctx.user)

    if json:
        click.echo(response.text)
    else:
        count = response.json()["count"]
        if count == 0:
            click.echo("You have no unread notifications")
        elif count == 1:
            click.echo("You have 1 unread notification")
        else:
            click.echo("You have {count} unread notifications")


@notifications.command()
@pass_context
@json_option
def policy(ctx: Context, json: bool):
    """Get the notifications filtering policy"""
    response = api.get_notifications_policy(ctx.app, ctx.user)

    if json:
        click.echo(response.text)
    else:
        policy = from_dict(NotificationPolicy, response.json())
        print_notification_policy(policy)


@notifications.command()
@click.option(
    "--for-not-following",
    type=POLICY_CHOICE,
    help="Policy for accounts the user is not following",
)
@click.option(
    "--for-not-followers",
    type=POLICY_CHOICE,
    help="Policy for accounts that are not following the user",
)
@click.option(
    "--for-new-accounts",
    type=POLICY_CHOICE,
    help="Policy for accounts created in the past 30 days",
)
@click.option(
    "--for-private-mentions",
    type=POLICY_CHOICE,
    help="Policy for private mentions",
)
@click.option(
    "--for-limited_accounts",
    type=POLICY_CHOICE,
    help="Policy for accounts that were limited by a moderator",
)
@pass_context
@json_option
def set_policy(
    ctx: Context,
    for_not_following: Optional[str],
    for_not_followers: Optional[str],
    for_new_accounts: Optional[str],
    for_private_mentions: Optional[str],
    for_limited_accounts: Optional[str],
    json: bool,
):
    """Update the filtering policy for notifications

    Each policy can be set to either `accept`, `filter` or `drop` notifications.

    \b
    - `drop` will prevent creation of the notification object altogether
    - `filter` will cause it to be marked as filtered
    - `accept` will not affect its processing
    """

    payload = drop_empty_values(
        {
            "for_not_following": for_not_following,
            "for_not_followers": for_not_followers,
            "for_new_accounts": for_new_accounts,
            "for_private_mentions": for_private_mentions,
            "for_limited_accounts": for_limited_accounts,
        }
    )

    if not payload:
        raise click.ClickException("At least one policy must be specified")

    response = api.set_notifications_policy(ctx.app, ctx.user, payload)

    if json:
        click.echo(response.text)
    else:
        click.echo("Policy updated!\n")
        policy = from_dict(NotificationPolicy, response.json())
        print_notification_policy(policy)


def print_notification_policy(policy: NotificationPolicy):
    click.echo(f"For not following:    {color_policy(policy.for_not_following)}")
    click.echo(f"For not followers:    {color_policy(policy.for_not_followers)}")
    click.echo(f"For new accounts:     {color_policy(policy.for_new_accounts)}")
    click.echo(f"For private mentions: {color_policy(policy.for_private_mentions)}")
    click.echo(f"For limited accounts: {color_policy(policy.for_limited_accounts)}")

    if policy.summary:
        summary = policy.summary
        click.echo("")
        click.echo(f"Pending requests: {summary.pending_requests_count}")
        click.echo(f"Pending notifications: {summary.pending_notifications_count}")


def color_policy(policy):
    if policy == "accept":
        return green(policy)
    if policy == "filter":
        return yellow(policy)
    if policy == "drop":
        return red(policy)
    return policy
