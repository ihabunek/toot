from typing import NamedTuple
import click
from toot.cli.base import Context, cli, pass_context
from toot.tui.app import TUI, TuiOptions

@cli.command()
@click.option(
    "--relative-datetimes",
    is_flag=True,
    help="Show relative datetimes in status list"
)
@pass_context
def tui(ctx: Context, relative_datetimes: bool):
    """Launches the toot terminal user interface"""
    options = TuiOptions(relative_datetimes, ctx.color)
    TUI.create(ctx.app, ctx.user, options).run()
