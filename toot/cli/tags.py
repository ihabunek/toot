import json as pyjson
from typing import Optional
from urllib.parse import quote

import click

from toot import api, http
from toot.cli import Context, cli, json_option, pass_context
from toot.cli.validators import validate_positive
from toot.entities import Status, Tag, from_dict, from_response_list, from_responses_batched
from toot.output import get_continue, green, print_tag_list, print_timeline, yellow
from toot.utils import drop_empty_values, str_bool_nullable


@cli.group()
def tags():
    """List, follow, and unfollow tags"""


@tags.command()
@click.argument("tag")
@json_option
@pass_context
def info(ctx: Context, tag, json: bool):
    """Show a hashtag and its associated information"""
    tag = api.find_tag(ctx.app, ctx.user, tag)

    if not tag:
        raise click.ClickException("Tag not found")

    if json:
        click.echo(pyjson.dumps(tag))
    else:
        tag = from_dict(Tag, tag)
        click.secho(f"#{tag.name}", fg="yellow")
        click.secho(tag.url, italic=True)
        if tag.following:
            click.echo("Followed")
        else:
            click.echo("Not followed")


@tags.command()
@json_option
@pass_context
def followed(ctx: Context, json: bool):
    """List followed tags"""
    tags = api.followed_tags(ctx.app, ctx.user)
    if json:
        click.echo(pyjson.dumps(tags))
    else:
        if tags:
            print_tag_list(tags)
        else:
            click.echo("You're not following any hashtags")


@tags.command()
@click.argument("tag")
@json_option
@pass_context
def follow(ctx: Context, tag: str, json: bool):
    """Follow a hashtag"""
    tag = tag.lstrip("#")
    response = api.follow_tag(ctx.app, ctx.user, tag)
    if json:
        click.echo(response.text)
    else:
        click.secho(f"✓ You are now following #{tag}", fg="green")


@tags.command()
@click.argument("tag")
@json_option
@pass_context
def unfollow(ctx: Context, tag: str, json: bool):
    """Unfollow a hashtag"""
    tag = tag.lstrip("#")
    response = api.unfollow_tag(ctx.app, ctx.user, tag)
    if json:
        click.echo(response.text)
    else:
        click.secho(f"✓ You are no longer following #{tag}", fg="green")


@tags.command()
@json_option
@pass_context
def featured(ctx: Context, json: bool):
    """List hashtags featured on your profile."""
    response = api.featured_tags(ctx.app, ctx.user)
    if json:
        click.echo(response.text)
    else:
        tags = response.json()
        if tags:
            print_tag_list(tags)
        else:
            click.echo("You don't have any featured hashtags")


@tags.command()
@click.argument("tag")
@json_option
@pass_context
def feature(ctx: Context, tag: str, json: bool):
    """Feature a hashtag on your profile"""
    tag = tag.lstrip("#")
    response = api.feature_tag(ctx.app, ctx.user, tag)
    if json:
        click.echo(response.text)
    else:
        click.secho(f"✓ Tag #{tag} is now featured", fg="green")


@tags.command()
@click.argument("tag")
@json_option
@pass_context
def unfeature(ctx: Context, tag: str, json: bool):
    """Unfollow a hashtag

    TAG can either be a tag name like "#foo" or "foo" or a tag ID.
    """
    featured_tag = api.find_featured_tag(ctx.app, ctx.user, tag)

    # TODO: should this be idempotent?
    if not featured_tag:
        raise click.ClickException(f"Tag {tag} is not featured")

    response = api.unfeature_tag(ctx.app, ctx.user, featured_tag["id"])
    if json:
        click.echo(response.text)
    else:
        click.secho(f"✓ Tag #{featured_tag['name']} is no longer featured", fg="green")


@tags.command()
@click.argument("tag_name")
@click.option(
    "-l",
    "--local",
    is_flag=True,
    help="Return only local statuses",
)
@click.option(
    "-r",
    "--remote",
    is_flag=True,
    help="Return only remote statuses",
)
@click.option(
    "-m",
    "--media",
    is_flag=True,
    help="Return only statuses with media attachments",
)
@click.option(
    "-n",
    "--limit",
    type=int,
    default=20,
    help="Number of results to fetch per request [max: 40]",
)
@click.option(
    "-p",
    "--pager",
    help="Page the results, optionally define how many results to show per page",
    type=int,
    callback=validate_positive,
    is_flag=False,
    flag_value=10,
)
@click.option(
    "-c",
    "--clear",
    help="Clear the screen before printing",
    is_flag=True,
)
@json_option
@pass_context
def timeline(
    ctx: Context,
    tag_name: str,
    local: bool,
    remote: bool,
    media: bool,
    limit: int,
    pager: Optional[int],
    clear: bool,
    json: bool,
):
    """View hashtag timeline"""
    # TODO: Add `any`, `all`, and `none` params
    # TODO: Add `max_id`, `since_id`, and `min_id` params
    path = f"/api/v1/timelines/tag/{quote(tag_name)}"

    params = drop_empty_values(
        {
            "local": str_bool_nullable(local),
            "remote": str_bool_nullable(remote),
            "media": str_bool_nullable(media),
            "limit": limit,
        }
    )

    if json:
        response = http.get(ctx.app, ctx.user, path, params)
        click.echo(response.text)
        return

    if pager:
        first = True
        printed_any = False

        responses = http.get_paged(ctx.app, ctx.user, path, params)
        for page in from_responses_batched(responses, Status, pager):
            if not first and not get_continue():
                break
            if clear:
                click.clear()
            print_timeline(page)
            first = False
            printed_any = True

        if not printed_any:
            click.echo("No statuses found containing the given tag")
        return

    response = http.get(ctx.app, ctx.user, path, params)
    statuses = from_response_list(Status, response)
    if statuses:
        print_timeline(statuses)
        if len(statuses) == limit:
            click.secho("There may be more results. Increase the --limit or use --pager to see the rest.", dim=True)
    else:
        click.echo("No statuses found containing the given tag")
