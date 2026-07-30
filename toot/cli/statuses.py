import os
from copy import copy
from datetime import datetime, timezone

import click

from toot import api
from toot.cli import cli, json_option, Context, pass_context
from toot.cli import VISIBILITY_CHOICES
from toot.cli.validators import validate_language
from toot.output import print_table
from toot.utils import editor_input
from toot.utils.datetime import parse_datetime


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


@cli.command()
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


@cli.command()
@click.argument("status_id")
@click.option(
    "--text", "-t",
    help="New text for the status. If not given and --editor is used, "
         "the current text is loaded into the editor."
)
@click.option(
    "--editor", "-e",
    is_flag=False,
    flag_value=os.getenv("EDITOR"),
    help="""Edit in an external editor. When used without a value it will use
            the editor defined in the $EDITOR environment variable."""
)
@click.option(
    "--visibility", "-v",
    type=click.Choice(VISIBILITY_CHOICES),
    help="New visibility for the status",
)
@click.option(
    "--sensitive", "-s",
    is_flag=True,
    default=None,
    help="Mark or unmark media as sensitive",
)
@click.option(
    "--spoiler-text", "-p",
    help="New content warning text",
)
@click.option(
    "--language", "-l",
    callback=validate_language,
    help="ISO 639-1 language code",
)
@click.option(
    "--content-type",
    help="MIME type for the status text (not supported on all instances)",
)
@json_option
@pass_context
def edit(ctx: Context, status_id: str, text: str, editor: str,
         visibility: str, sensitive: bool, spoiler_text: str,
         language: str, content_type: str, json: bool):
    """Edit an existing status

    Edits the text, visibility, or other properties of a status you have
    posted. Use --editor to open an external editor pre-filled with the
    current status text.
    """
    if editor and not text:
        source = api.fetch_status_source(ctx.app, ctx.user, status_id).json()
        text = editor_input(editor, source.get("text", ""))
    elif not text and not editor:
        raise click.ClickException(
            "Provide --text or --editor to change the status text."
        )

    # Fetch original status to preserve poll data when editing
    original = api.fetch_status(ctx.app, ctx.user, status_id).json()
    poll_args = {}
    poll = original.get("poll")
    if poll is not None:
        poll_args["poll_options"] = [o["title"] for o in poll["options"]]
        poll_args["poll_multiple"] = poll["multiple"]

        expires_at = parse_datetime(poll["expires_at"])
        expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())
        poll_args["poll_expires_in"] = expires_in

        if "hide_totals" in poll:
            poll_args["poll_hide_totals"] = poll["hide_totals"]

    response = api.edit_status(
        ctx.app,
        ctx.user,
        status_id,
        text,
        visibility=visibility,
        sensitive=sensitive,
        spoiler_text=spoiler_text,
        language=language,
        content_type=content_type,
        **poll_args,
    )

    if json:
        click.echo(response.text)
    else:
        click.secho("✓ Status edited", fg="green")


# Make alias in snake case to keep BC
reblogged_by_alias = copy(reblogged_by)
reblogged_by_alias.hidden = True
cli.add_command(reblogged_by_alias, name="reblogged_by")
