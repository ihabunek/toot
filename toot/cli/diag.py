import click
from toot.output import print_diags
from toot.cli import (
    cli,
    pass_context,
    Context,
)


@cli.command()
@click.option(
    "-f",
    "--files",
    is_flag=True,
    help="Print contents of the config and settings files in diagnostic output",
)
@pass_context
def diag(ctx: Context, files: bool):
    """Display useful information for diagnosing problems"""

    print_diags(files)
