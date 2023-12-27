import click
import logging
import os
import sys
import typing as t

from click.testing import Result
from functools import wraps
from toot import App, User, config, __version__
from toot.settings import get_settings
from toot.output import print_warning

if t.TYPE_CHECKING:
    import typing_extensions as te
    P = te.ParamSpec("P")

R = t.TypeVar("R")
T = t.TypeVar("T")


PRIVACY_CHOICES = ["public", "unlisted", "private"]
VISIBILITY_CHOICES = ["public", "unlisted", "private", "direct"]

TUI_COLORS = {
    "1": 1,
    "16": 16,
    "88": 88,
    "256": 256,
    "16777216": 16777216,
    "24bit": 16777216,
}
TUI_COLORS_CHOICES = list(TUI_COLORS.keys())
TUI_COLORS_VALUES = list(TUI_COLORS.values())

DURATION_EXAMPLES = """e.g. "1 day", "2 hours 30 minutes", "5 minutes 30
seconds" or any combination of above. Shorthand: "1d", "2h30m", "5m30s\""""


# Type alias for run commands
Run = t.Callable[..., Result]


def get_default_visibility() -> str:
    return os.getenv("TOOT_POST_VISIBILITY", "public")


def get_default_map():
    settings = get_settings()
    common = settings.get("common", {})
    commands = settings.get("commands", {})

    # TODO: remove in version 1.0
    tui_old = settings.get("tui", {})

    # Remove palette to avoid triggering warning for still valid [tui.palette] section
    if "palette" in tui_old:
        del tui_old["palette"]

    if tui_old:
        print_warning("Settings section [tui] has been deprecated in favour of [commands.tui].")
        tui_new = commands.get("tui", {})
        commands["tui"] = {**tui_old, **tui_new}

    return {**common, **commands}


# Tweak the Click context
# https://click.palletsprojects.com/en/8.1.x/api/#context
CONTEXT = dict(
    # Enable using environment variables to set options
    auto_envvar_prefix="TOOT",
    # Add shorthand -h for invoking help
    help_option_names=["-h", "--help"],
    # Always show default values for options
    show_default=True,
    # Load command defaults from settings
    default_map=get_default_map(),
)


class Context(t.NamedTuple):
    app: t.Optional[App]
    user: t.Optional[User] = None
    color: bool = False
    debug: bool = False


class TootObj(t.NamedTuple):
    """Data to add to Click context"""
    color: bool = True
    debug: bool = False
    # Pass a context for testing purposes
    test_ctx: t.Optional[Context] = None


def pass_context(f: "t.Callable[te.Concatenate[Context, P], R]") -> "t.Callable[P, R]":
    """Pass the toot Context as first argument."""
    @wraps(f)
    def wrapped(*args: "P.args", **kwargs: "P.kwargs") -> R:
        return f(get_context(), *args, **kwargs)

    return wrapped


def get_context() -> Context:
    click_context = click.get_current_context()
    obj: TootObj = click_context.obj

    # This is used to pass a context for testing, not used in normal usage
    if obj.test_ctx:
        return obj.test_ctx

    user, app = config.get_active_user_app()
    if not user or not app:
        raise click.ClickException("This command requires you to be logged in.")

    return Context(app, user, obj.color, obj.debug)


json_option = click.option(
    "--json",
    is_flag=True,
    default=False,
    help="Print data as JSON rather than human readable text"
)


@click.group(context_settings=CONTEXT)
@click.option("-w", "--max-width", type=int, default=80, help="Maximum width for content rendered by toot")
@click.option("--debug/--no-debug", default=False, help="Log debug info to stderr")
@click.option("--color/--no-color", default=sys.stdout.isatty(), help="Use ANSI color in output")
@click.version_option(__version__, message="%(prog)s v%(version)s")
@click.pass_context
def cli(ctx: click.Context, max_width: int, color: bool, debug: bool):
    """Toot is a Mastodon CLI"""
    ctx.obj = TootObj(color, debug)
    ctx.color = color
    ctx.max_content_width = max_width

    if debug:
        logging.basicConfig(level=logging.DEBUG)


from toot.cli import accounts  # noqa
from toot.cli import auth  # noqa
from toot.cli import lists  # noqa
from toot.cli import post  # noqa
from toot.cli import read  # noqa
from toot.cli import statuses  # noqa
from toot.cli import tags  # noqa
from toot.cli import timelines  # noqa
from toot.cli import tui  # noqa
