import click
import json as pyjson

from toot import api
from toot.cli import cli, json_option, Context, pass_context
from toot.output import print_acct_list


@cli.group(name="follow_request")
def follow_request():
    """Manage follow requests"""
    pass


@follow_request.command(name="accept")
@click.argument("account")
@json_option
@pass_context
def accept_follow_request(ctx: Context, account: str, json: bool):
    """Accept follow request from an account"""
    found_account = api.find_account(ctx.app, ctx.user, account)
    response = api.accept_follow_request(ctx.app, ctx.user, found_account["id"])
    if json:
        click.echo(response.text)
    else:
        click.secho(f"✓ {account} is now following you", fg="green")


@follow_request.command(name="reject")
@click.argument("account")
@json_option
@pass_context
def reject_follow_request(ctx: Context, account: str, json: bool):
    """Reject follow request from an account"""
    found_account = api.find_account(ctx.app, ctx.user, account)
    response = api.reject_follow_request(ctx.app, ctx.user, found_account["id"])
    if json:
        click.echo(response.text)
    else:
        click.secho(f"✓ follow request from {account} rejected", fg="green")


@follow_request.command(name="list")
@json_option
@pass_context
def list_follow_requests(ctx: Context, json: bool):
    """List follow requests"""
    requests = api.list_follow_requests(ctx.app, ctx.user)
    if json:
        click.echo(pyjson.dumps(requests))
    else:
        print_acct_list(requests)
