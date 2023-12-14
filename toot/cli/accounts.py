import click
import json as pyjson

from typing import BinaryIO, Optional

from toot import api
from toot.cli import PRIVACY_CHOICES, cli, json_option, Context, pass_context
from toot.cli.validators import validate_language
from toot.output import print_acct_list


@cli.command(name="update_account")
@click.option("--display-name", help="The display name to use for the profile.")
@click.option("--note", help="The account bio.")
@click.option(
    "--avatar",
    type=click.File(mode="rb"),
    help="Path to the avatar image to set.",
)
@click.option(
    "--header",
    type=click.File(mode="rb"),
    help="Path to the header image to set.",
)
@click.option(
    "--bot/--no-bot",
    default=None,
    help="Whether the account has a bot flag.",
)
@click.option(
    "--discoverable/--no-discoverable",
    default=None,
    help="Whether the account should be shown in the profile directory.",
)
@click.option(
    "--locked/--no-locked",
    default=None,
    help="Whether manual approval of follow requests is required.",
)
@click.option(
    "--privacy",
    type=click.Choice(PRIVACY_CHOICES),
    help="Default post privacy for authored statuses.",
)
@click.option(
    "--sensitive/--no-sensitive",
    default=None,
    help="Whether to mark authored statuses as sensitive by default.",
)
@click.option(
    "--language",
    callback=validate_language,
    help="Default language to use for authored statuses (ISO 639-1).",
)
@json_option
@pass_context
def update_account(
    ctx: Context,
    display_name: Optional[str],
    note: Optional[str],
    avatar: Optional[BinaryIO],
    header: Optional[BinaryIO],
    bot: Optional[bool],
    discoverable: Optional[bool],
    locked: Optional[bool],
    privacy: Optional[bool],
    sensitive: Optional[bool],
    language: Optional[bool],
    json: bool,
):
    """Update your account details"""
    options = [
        avatar,
        bot,
        discoverable,
        display_name,
        header,
        language,
        locked,
        note,
        privacy,
        sensitive,
    ]

    if all(option is None for option in options):
        raise click.ClickException("Please specify at least one option to update the account")

    response = api.update_account(
        ctx.app,
        ctx.user,
        avatar=avatar,
        bot=bot,
        discoverable=discoverable,
        display_name=display_name,
        header=header,
        language=language,
        locked=locked,
        note=note,
        privacy=privacy,
        sensitive=sensitive,
    )

    if json:
        click.echo(response.text)
    else:
        click.secho("✓ Account updated", fg="green")


@cli.command()
@click.argument("account")
@json_option
@pass_context
def follow(ctx: Context, account: str, json: bool):
    """Follow an account"""
    found_account = api.find_account(ctx.app, ctx.user, account)
    response = api.follow(ctx.app, ctx.user, found_account["id"])
    if json:
        click.echo(response.text)
    else:
        click.secho(f"✓ You are now following {account}", fg="green")


@cli.command()
@click.argument("account")
@json_option
@pass_context
def unfollow(ctx: Context, account: str, json: bool):
    """Unfollow an account"""
    found_account = api.find_account(ctx.app, ctx.user, account)
    response = api.unfollow(ctx.app, ctx.user, found_account["id"])
    if json:
        click.echo(response.text)
    else:
        click.secho(f"✓ You are no longer following {account}", fg="green")


@cli.command()
@click.argument("account", required=False)
@json_option
@pass_context
def following(ctx: Context, account: Optional[str], json: bool):
    """List accounts followed by an account.

    If no account is given list accounts followed by you.
    """
    account = account or ctx.user.username
    found_account = api.find_account(ctx.app, ctx.user, account)
    accounts = api.following(ctx.app, ctx.user, found_account["id"])
    if json:
        click.echo(pyjson.dumps(accounts))
    else:
        print_acct_list(accounts)


@cli.command()
@click.argument("account", required=False)
@json_option
@pass_context
def followers(ctx: Context, account: Optional[str], json: bool):
    """List accounts following an account.

    If no account given list accounts following you."""
    account = account or ctx.user.username
    found_account = api.find_account(ctx.app, ctx.user, account)
    accounts = api.followers(ctx.app, ctx.user, found_account["id"])
    if json:
        click.echo(pyjson.dumps(accounts))
    else:
        print_acct_list(accounts)


@cli.command()
@click.argument("account")
@json_option
@pass_context
def mute(ctx: Context, account: str, json: bool):
    """Mute an account"""
    found_account = api.find_account(ctx.app, ctx.user, account)
    response = api.mute(ctx.app, ctx.user, found_account["id"])
    if json:
        click.echo(response.text)
    else:
        click.secho(f"✓ You have muted {account}", fg="green")


@cli.command()
@click.argument("account")
@json_option
@pass_context
def unmute(ctx: Context, account: str, json: bool):
    """Unmute an account"""
    found_account = api.find_account(ctx.app, ctx.user, account)
    response = api.unmute(ctx.app, ctx.user, found_account["id"])
    if json:
        click.echo(response.text)
    else:
        click.secho(f"✓ {account} is no longer muted", fg="green")


@cli.command()
@json_option
@pass_context
def muted(ctx: Context, json: bool):
    """List muted accounts"""
    response = api.muted(ctx.app, ctx.user)
    if json:
        click.echo(pyjson.dumps(response))
    else:
        if len(response) > 0:
            click.echo("Muted accounts:")
            print_acct_list(response)
        else:
            click.echo("No accounts muted")


@cli.command()
@click.argument("account")
@json_option
@pass_context
def block(ctx: Context, account: str, json: bool):
    """Block an account"""
    found_account = api.find_account(ctx.app, ctx.user, account)
    response = api.block(ctx.app, ctx.user, found_account["id"])
    if json:
        click.echo(response.text)
    else:
        click.secho(f"✓ You are now blocking {account}", fg="green")


@cli.command()
@click.argument("account")
@json_option
@pass_context
def unblock(ctx: Context, account: str, json: bool):
    """Unblock an account"""
    found_account = api.find_account(ctx.app, ctx.user, account)
    response = api.unblock(ctx.app, ctx.user, found_account["id"])
    if json:
        click.echo(response.text)
    else:
        click.secho(f"✓ {account} is no longer blocked", fg="green")


@cli.command()
@json_option
@pass_context
def blocked(ctx: Context, json: bool):
    """List blocked accounts"""
    response = api.blocked(ctx.app, ctx.user)
    if json:
        click.echo(pyjson.dumps(response))
    else:
        if len(response) > 0:
            click.echo("Blocked accounts:")
            print_acct_list(response)
        else:
            click.echo("No accounts blocked")
