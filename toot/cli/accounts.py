import click
import json as pyjson

from typing import Optional

from toot import api
from toot.cli.base import cli, json_option, Context, pass_context
from toot.output import print_acct_list


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
