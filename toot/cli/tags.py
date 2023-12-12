import click
import json as pyjson

from toot import api
from toot.cli.base import cli, pass_context, json_option, Context
from toot.output import print_tag_list, print_warning


@cli.group(invoke_without_command=True)
@json_option
@click.pass_context
def tags(ctx: click.Context, json):
    """List, follow, and unfollow tags

    When invoked without a command, lists followed tags."""
    if ctx.invoked_subcommand is None:
        tags = api.followed_tags(ctx.obj.app, ctx.obj.user)
        if json:
            click.echo(pyjson.dumps(tags))
        else:
            print_tag_list(tags)


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


# -- Deprecated commands -------------------------------------------------------

@cli.command(name="tags_followed", hidden=True)
@pass_context
def tags_followed(ctx: Context):
    """List hashtags you follow"""
    print_warning("`toot tags_followed` is deprecated in favour of `toot tags`")
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
