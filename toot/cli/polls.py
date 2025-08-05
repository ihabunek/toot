import json as pyjson

import click

from toot import api
from toot.cli import Context, cli, json_option, pass_context
from toot.entities import Poll, from_dict
from toot.output import print_poll


@cli.group()
def polls():
    """Show and vote on polls"""
    pass

@polls.command()
@click.argument("poll_id")
@json_option
@pass_context
def show(ctx: Context, poll_id: str, json: bool):
    """Show a poll by ID"""
    data = api.get_poll(ctx.app, ctx.user, poll_id)

    if json:
        click.echo(pyjson.dumps(data))
    else:
        poll = from_dict(Poll, data)
        print_poll(poll)
