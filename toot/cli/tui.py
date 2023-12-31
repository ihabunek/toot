import click

from typing import Optional
from toot.cli import TUI_COLORS, VISIBILITY_CHOICES, Context, cli, pass_context
from toot.cli.validators import validate_tui_colors
from toot.tui.app import TUI, TuiOptions

COLOR_OPTIONS = ", ".join(TUI_COLORS.keys())


@cli.command()
@click.option(
    "-r", "--relative-datetimes",
    is_flag=True,
    help="Show relative datetimes in status list"
)
@click.option(
    "-m", "--media-viewer",
    help="Program to invoke with media URLs to display the media files, such as 'feh'"
)
@click.option(
    "-c", "--colors",
    callback=validate_tui_colors,
    help=f"""Number of colors to use, one of {COLOR_OPTIONS}, defaults to 16 if
             using --color, and 1 if using --no-color."""
)
@click.option(
    "-v", "--default-visibility",
    type=click.Choice(VISIBILITY_CHOICES),
    help="Default visibility when posting new toots; overrides the server-side preference"
)
@pass_context
def tui(
    ctx: Context,
    colors: Optional[int],
    media_viewer: Optional[str],
    relative_datetimes: bool,
    default_visibility: Optional[str]
):
    """Launches the toot terminal user interface"""
    if colors is None:
        colors = 16 if ctx.color else 1

    options = TuiOptions(
        colors=colors,
        media_viewer=media_viewer,
        relative_datetimes=relative_datetimes,
        default_visibility=default_visibility
    )
    tui = TUI.create(ctx.app, ctx.user, options)
    tui.run()
