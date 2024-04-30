from aiohttp import ClientSession
import click
import json as pyjson

from itertools import chain
from typing import Optional

from toot import api, ahttp
from toot.cli.validators import validate_instance
from toot.entities import Instance, Status, from_dict, Account, from_response
from toot.exceptions import ApiError, ConsoleError
from toot.output import print_account, print_instance, print_search_results, print_status, print_timeline
from toot.cli import InstanceParamType, async_command, cli, get_context, json_option, pass_context, Context, pass_session


@cli.command()
@json_option
@async_command
@pass_session
async def whoami(session: ClientSession, json: bool):
    """Display logged in user details"""
    response = await ahttp.verify_credentials(session)
    response.raise_for_status()

    if json:
        click.echo(await response.text())
    else:
        account = await from_response(Account, response)
        print_account(account)


@cli.command()
@click.argument("account")
@json_option
@async_command
@pass_session
async def whois(session: ClientSession, account: str, json: bool):
    """Display account details"""
    account_dict = ahttp.find_account(ctx.app, ctx.user, account)

    # Here it's not possible to avoid parsing json since it's needed to find the account.
    if json:
        click.echo(pyjson.dumps(account_dict))
    else:
        account_obj = from_dict(Account, account_dict)
        print_account(account_obj)


@cli.command()
@click.argument("instance", type=InstanceParamType(), callback=validate_instance, required=False)
@json_option
def instance(instance: Optional[str], json: bool):
    """Display instance details

    INSTANCE can be a domain or base URL of the instance to display.
    e.g. 'mastodon.social' or 'https://mastodon.social'. If not
    given will display details for the currently logged in instance.
    """
    if not instance:
        context = get_context()
        if not context.app:
            raise click.ClickException("INSTANCE argument not given and not logged in")
        instance = context.app.base_url

    try:
        response = api.get_instance(instance)
    except ApiError:
        raise ConsoleError(
            f"Instance not found at {instance}.\n" +
            "The given domain probably does not host a Mastodon instance."
        )

    if json:
        click.echo(response.text)
    else:
        print_instance(from_dict(Instance, response.json()))


@cli.command()
@click.argument("query")
@click.option("-r", "--resolve", is_flag=True, help="Resolve non-local accounts")
@json_option
@pass_context
def search(ctx: Context, query: str, resolve: bool, json: bool):
    """Search for users or hashtags"""
    response = api.search(ctx.app, ctx.user, query, resolve)
    if json:
        click.echo(response.text)
    else:
        print_search_results(response.json())


@cli.command()
@click.argument("status_id")
@json_option
@async_command
@pass_session
async def status(session: ClientSession, status_id: str, json: bool):
    """Show a single status"""
    response = await ahttp.fetch_status(session, status_id)
    response.raise_for_status()

    if json:
        click.echo(await response.text())
    else:
        status = from_dict(Status, await response.json())
        print_status(status)


@cli.command()
@click.argument("status_id")
@json_option
@pass_context
def thread(ctx: Context, status_id: str, json: bool):
    """Show thread for a toot."""
    context_response = api.context(ctx.app, ctx.user, status_id)
    if json:
        click.echo(context_response.text)
    else:
        toot = api.fetch_status(ctx.app, ctx.user, status_id).json()
        context = context_response.json()

        statuses = chain(context["ancestors"], [toot], context["descendants"])
        print_timeline(from_dict(Status, s) for s in statuses)
