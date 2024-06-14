from toot.output import print_diags
from toot.cli import (
    cli,
    pass_context,
    Context,
)


@cli.command()
@pass_context
def diag(ctx: Context):
    """Display useful information for diagnosing problems"""

    print_diags()
