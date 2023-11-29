import click

from toot import api
from toot.cli.base import Context, cli, pass_context
from toot.output import print_list_accounts, print_lists


@cli.command()
@pass_context
def lists(ctx: Context):
    """List all lists"""
    lists = api.get_lists(ctx.app, ctx.user)

    if lists:
        print_lists(lists)
    else:
        click.echo("You have no lists defined.")


@cli.command(name="list_accounts")
@click.argument("title", required=False)
@click.option("--id", help="List ID if not title is given")
@pass_context
def list_accounts(ctx: Context, title: str, id: str):
    """List the accounts in a list"""
    list_id = _get_list_id(ctx, title, id)
    response = api.get_list_accounts(ctx.app, ctx.user, list_id)
    print_list_accounts(response)


@cli.command(name="list_create")
@click.argument("title")
@click.option(
    "--replies-policy",
    type=click.Choice(["followed", "list", "none"]),
    default="none",
    help="Replies policy"
)
@pass_context
def list_create(ctx: Context, title: str, replies_policy: str):
    """Create a list"""
    api.create_list(ctx.app, ctx.user, title=title, replies_policy=replies_policy)
    click.secho(f"✓ List \"{title}\" created.", fg="green")


@cli.command(name="list_delete")
@click.argument("title", required=False)
@click.option("--id", help="List ID if not title is given")
@pass_context
def list_delete(ctx: Context, title: str, id: str):
    """Delete a list"""
    list_id = _get_list_id(ctx, title, id)
    api.delete_list(ctx.app, ctx.user, list_id)
    click.secho(f"✓ List \"{title if title else id}\" deleted.", fg="green")


@cli.command(name="list_add")
@click.argument("title", required=False)
@click.argument("account")
@click.option("--id", help="List ID if not title is given")
@pass_context
def list_add(ctx: Context, title: str, account: str, id: str):
    """Add an account to a list"""
    list_id = _get_list_id(ctx, title, id)
    found_account = api.find_account(ctx.app, ctx.user, account)

    try:
        api.add_accounts_to_list(ctx.app, ctx.user, list_id, [found_account["id"]])
    except Exception:
        # if we failed to add the account, try to give a
        # more specific error message than "record not found"
        my_accounts = api.followers(ctx.app, ctx.user, found_account["id"])
        found = False
        if my_accounts:
            for my_account in my_accounts:
                if my_account["id"] == found_account["id"]:
                    found = True
                    break
        if found is False:
            raise click.ClickException(f"You must follow @{account} before adding this account to a list.")
        raise

    click.secho(f"✓ Added account \"{account}\"", fg="green")


@cli.command(name="list_remove")
@click.argument("title", required=False)
@click.argument("account")
@click.option("--id", help="List ID if not title is given")
@pass_context
def list_remove(ctx: Context, title: str, account: str, id: str):
    """Remove an account from a list"""
    list_id = _get_list_id(ctx, title, id)
    found_account = api.find_account(ctx.app, ctx.user, account)
    api.remove_accounts_from_list(ctx.app, ctx.user, list_id, [found_account["id"]])
    click.secho(f"✓ Removed account \"{account}\"", fg="green")


def _get_list_id(ctx: Context, title, list_id):
    if not list_id:
        list_id = api.find_list_id(ctx.app, ctx.user, title)
    if not list_id:
        raise click.ClickException("List not found")
    return list_id
