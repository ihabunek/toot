import json as pyjson

import click

from toot import api
from toot.cli import Context, cli, json_option, pass_context
from toot.output import print_acct_list


@cli.group()
def follow_requests():
    """Manage follow requests"""
    pass


@follow_requests.command()
@click.argument("account")
@json_option
@pass_context
def accept(ctx: Context, account: str, json: bool):
    """Accept follow request from an account"""
    found_account = api.find_account(ctx.app, ctx.user, account)
    response = api.accept_follow_request(ctx.app, ctx.user, found_account["id"])
    if json:
        click.echo(response.text)
    else:
        click.secho(f"✓ {account} is now following you", fg="green")


@follow_requests.command()
@click.argument("account")
@json_option
@pass_context
def reject(ctx: Context, account: str, json: bool):
    """Reject follow request from an account"""
    found_account = api.find_account(ctx.app, ctx.user, account)
    response = api.reject_follow_request(ctx.app, ctx.user, found_account["id"])
    if json:
        click.echo(response.text)
    else:
        click.secho(f"✓ follow request from {account} rejected", fg="green")


@follow_requests.command()
@json_option
@pass_context
def list(ctx: Context, json: bool):
    """List follow requests"""
    requests = api.list_follow_requests(ctx.app, ctx.user)
    if json:
        click.echo(pyjson.dumps(requests))
    else:
        print_acct_list(requests)
