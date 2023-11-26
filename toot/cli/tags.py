import click

from toot import api
from toot.cli.base import cli, pass_context, Context
from toot.output import print_tag_list


@cli.command(name="tags_followed")
@pass_context
def tags_followed(ctx: Context):
    """List hashtags you follow"""
    response = api.followed_tags(ctx.app, ctx.user)
    print_tag_list(response)


@cli.command(name="tags_follow")
@click.argument("tag")
@pass_context
def tags_follow(ctx: Context, tag: str):
    """Follow a hashtag"""
    tag = tag.lstrip("#")
    api.follow_tag(ctx.app, ctx.user, tag)
    click.secho(f"✓ You are now following #{tag}", fg="green")


@cli.command(name="tags_unfollow")
@click.argument("tag")
@pass_context
def tags_unfollow(ctx: Context, tag: str):
    """Unfollow a hashtag"""
    tag = tag.lstrip("#")
    api.unfollow_tag(ctx.app, ctx.user, tag)
    click.secho(f"✓ You are no longer following #{tag}", fg="green")
