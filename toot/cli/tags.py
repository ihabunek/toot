import click

from toot import api
from toot.cli.base import cli, pass_context, Context
from toot.output import print_tag_list, print_warning


@cli.group(invoke_without_command=True)
@click.pass_context
def tags(ctx: click.Context):
    """List, follow, and unfollow tags

    When invoked without a command, lists followed tags."""
    if ctx.invoked_subcommand is None:
        response = api.followed_tags(ctx.obj.app, ctx.obj.user)
        print_tag_list(response)


@tags.command()
@click.argument("tag")
@pass_context
def follow(ctx: Context, tag: str):
    """Follow a hashtag"""
    tag = tag.lstrip("#")
    api.follow_tag(ctx.app, ctx.user, tag)
    click.secho(f"✓ You are now following #{tag}", fg="green")


@tags.command()
@click.argument("tag")
@pass_context
def unfollow(ctx: Context, tag: str):
    """Unfollow a hashtag"""
    tag = tag.lstrip("#")
    api.unfollow_tag(ctx.app, ctx.user, tag)
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
