import click
from toot import api
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
@click.option(
    "-s",
    "--server",
    is_flag=True,
    help="Print information about the curren server in diagnostic output",
)
@pass_context
def diag(ctx: Context, files: bool, server: bool):
    """Display useful information for diagnosing problems"""

    instance_dict = api.get_instance(ctx.app.base_url).json() if server else None
    print_diags(instance_dict, files)
