from typing import Tuple

import click

from toot import api
from toot.cli import Context, cli, json_option, pass_context
from toot.entities import Poll, from_response
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
    response = api.get_poll(ctx.app, ctx.user, poll_id)

    if json:
        click.echo(response.text)
    else:
        poll = from_response(Poll, response)
        print_poll(poll)


@polls.command()
@click.argument("poll_id")
@click.argument("choices", type=int, nargs=-1, required=True)
@json_option
@pass_context
def vote(ctx: Context, poll_id: str, choices: Tuple[int], json: bool):
    """Vote on a poll

    CHOICES is one or more zero-indexed integers corresponding to the desired poll choices.

    e.g. to vote for the first and third options use:

        toot polls vote <poll_id> 0 2
    """
    response = api.vote_poll(ctx.app, ctx.user, poll_id, choices)

    if json:
        click.echo(response.text)
    else:
        poll = from_response(Poll, response)
        click.echo("You voted!\n")
        print_poll(poll)
