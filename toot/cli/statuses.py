import click

from toot import api
from toot.cli import cli, json_option, Context, pass_context
from toot.cli import VISIBILITY_CHOICES
from toot.output import print_table


@cli.command()
@click.argument("status_id")
@json_option
@pass_context
def delete(ctx: Context, status_id: str, json: bool):
    """Delete a status"""
    response = api.delete_status(ctx.app, ctx.user, status_id)
    if json:
        click.echo(response.text)
    else:
        click.secho("✓ Status deleted", fg="green")


@cli.command()
@click.argument("status_id")
@json_option
@pass_context
def favourite(ctx: Context, status_id: str, json: bool):
    """Favourite a status"""
    response = api.favourite(ctx.app, ctx.user, status_id)
    if json:
        click.echo(response.text)
    else:
        click.secho("✓ Status favourited", fg="green")


@cli.command()
@click.argument("status_id")
@json_option
@pass_context
def unfavourite(ctx: Context, status_id: str, json: bool):
    """Unfavourite a status"""
    response = api.unfavourite(ctx.app, ctx.user, status_id)
    if json:
        click.echo(response.text)
    else:
        click.secho("✓ Status unfavourited", fg="green")


@cli.command()
@click.argument("status_id")
@click.option(
    "--visibility", "-v",
    help="Post visibility",
    type=click.Choice(VISIBILITY_CHOICES),
    default="public",
)
@json_option
@pass_context
def reblog(ctx: Context, status_id: str, visibility: str, json: bool):
    """Reblog (boost) a status"""
    response = api.reblog(ctx.app, ctx.user, status_id, visibility=visibility)
    if json:
        click.echo(response.text)
    else:
        click.secho("✓ Status reblogged", fg="green")


@cli.command()
@click.argument("status_id")
@json_option
@pass_context
def unreblog(ctx: Context, status_id: str, json: bool):
    """Unreblog (unboost) a status"""
    response = api.unreblog(ctx.app, ctx.user, status_id)
    if json:
        click.echo(response.text)
    else:
        click.secho("✓ Status unreblogged", fg="green")


@cli.command()
@click.argument("status_id")
@json_option
@pass_context
def pin(ctx: Context, status_id: str, json: bool):
    """Pin a status"""
    response = api.pin(ctx.app, ctx.user, status_id)
    if json:
        click.echo(response.text)
    else:
        click.secho("✓ Status pinned", fg="green")


@cli.command()
@click.argument("status_id")
@json_option
@pass_context
def unpin(ctx: Context, status_id: str, json: bool):
    """Unpin a status"""
    response = api.unpin(ctx.app, ctx.user, status_id)
    if json:
        click.echo(response.text)
    else:
        click.secho("✓ Status unpinned", fg="green")


@cli.command()
@click.argument("status_id")
@json_option
@pass_context
def bookmark(ctx: Context, status_id: str, json: bool):
    """Bookmark a status"""
    response = api.bookmark(ctx.app, ctx.user, status_id)
    if json:
        click.echo(response.text)
    else:
        click.secho("✓ Status bookmarked", fg="green")


@cli.command()
@click.argument("status_id")
@json_option
@pass_context
def unbookmark(ctx: Context, status_id: str, json: bool):
    """Unbookmark a status"""
    response = api.unbookmark(ctx.app, ctx.user, status_id)
    if json:
        click.echo(response.text)
    else:
        click.secho("✓ Status unbookmarked", fg="green")


@cli.command(name="reblogged_by")
@click.argument("status_id")
@json_option
@pass_context
def reblogged_by(ctx: Context, status_id: str, json: bool):
    """Show accounts that reblogged a status"""
    response = api.reblogged_by(ctx.app, ctx.user, status_id)

    if json:
        click.echo(response.text)
    else:
        rows = [[a["acct"], a["display_name"]] for a in response.json()]
        if rows:
            headers = ["Account", "Display name"]
            print_table(headers, rows)
        else:
            click.echo("This status is not reblogged by anyone")
