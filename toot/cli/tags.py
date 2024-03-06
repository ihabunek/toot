import click
import json as pyjson

from toot import api
from toot.cli import cli, pass_context, json_option, Context
from toot.entities import Tag, from_dict
from toot.output import print_tag_list, print_warning


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


# -- Deprecated commands -------------------------------------------------------

@cli.command(name="tags_followed", hidden=True)
@pass_context
def tags_followed(ctx: Context):
    """List hashtags you follow"""
    print_warning("`toot tags_followed` is deprecated in favour of `toot tags followed`")
    response = api.followed_tags(ctx.app, ctx.user)
    print_tag_list(response)


@cli.command(name="tags_follow", hidden=True)
@click.argument("tag")
@pass_context
def tags_follow(ctx: Context, tag: str):
    """Follow a hashtag"""
    print_warning("`toot tags_follow` is deprecated in favour of `toot tags follow`")
    tag = tag.lstrip("#")
    api.follow_tag(ctx.app, ctx.user, tag)
    click.secho(f"✓ You are now following #{tag}", fg="green")


@cli.command(name="tags_unfollow", hidden=True)
@click.argument("tag")
@pass_context
def tags_unfollow(ctx: Context, tag: str):
    """Unfollow a hashtag"""
    print_warning("`toot tags_unfollow` is deprecated in favour of `toot tags unfollow`")
    tag = tag.lstrip("#")
    api.unfollow_tag(ctx.app, ctx.user, tag)
    click.secho(f"✓ You are no longer following #{tag}", fg="green")
