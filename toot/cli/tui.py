import click

from typing import Optional
from toot.cli import TUI_COLORS, VISIBILITY_CHOICES, IMAGE_FORMAT_CHOICES, Context, cli, pass_context
from toot.cli.validators import validate_tui_colors, validate_cache_size
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
    "-s", "--cache-size",
    callback=validate_cache_size,
    help="""Specify the image cache maximum size in megabytes. Default: 10MB.
      Minimum: 1MB."""
)
@click.option(
    "-v", "--default-visibility",
    type=click.Choice(VISIBILITY_CHOICES),
    help="Default visibility when posting new toots; overrides the server-side preference"
)
@click.option(
    "-s", "--always-show-sensitive",
    is_flag=True,
    help="Expand toots with content warnings automatically"
)
@click.option(
    "-f", "--image-format",
    type=click.Choice(IMAGE_FORMAT_CHOICES),
    help="Image output format; support varies across terminals. Default: block"
)
@click.option(
    "--show-display-names",
    is_flag=True,
    default=False,
    help="Show display names instead of account names in the list view."
)
@pass_context
def tui(
    ctx: Context,
    colors: Optional[int],
    media_viewer: Optional[str],
    always_show_sensitive: bool,
    relative_datetimes: bool,
    cache_size: Optional[int],
    default_visibility: Optional[str],
    image_format: Optional[str],
    show_display_names: bool,
):
    """Launches the toot terminal user interface"""
    if colors is None:
        colors = 16 if ctx.color else 1

    options = TuiOptions(
        colors=colors,
        media_viewer=media_viewer,
        relative_datetimes=relative_datetimes,
        cache_size=cache_size,
        default_visibility=default_visibility,
        always_show_sensitive=always_show_sensitive,
        image_format=image_format,
        show_display_names=show_display_names,
    )
    tui = TUI.create(ctx.app, ctx.user, options)
    tui.run()
