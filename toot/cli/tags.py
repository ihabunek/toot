import json as pyjson

import click

from toot import api
from toot.cli import Context, cli, json_option, pass_context
from toot.entities import Tag, from_dict
from toot.output import print_tag_list


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
