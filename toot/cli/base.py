import click
import logging
import os
import sys
import typing as t

from click.testing import Result
from functools import wraps
from toot import App, User, config, __version__
from toot.settings import get_settings

if t.TYPE_CHECKING:
    import typing_extensions as te
    P = te.ParamSpec("P")

R = t.TypeVar("R")
T = t.TypeVar("T")


PRIVACY_CHOICES = ["public", "unlisted", "private"]
VISIBILITY_CHOICES = ["public", "unlisted", "private", "direct"]

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
    return {**common, **commands}


# Tweak the Click context
# https://click.palletsprojects.com/en/8.1.x/api/#context
CONTEXT = dict(
    # Enable using environment variables to set options
    auto_envvar_prefix="TOOT",
    # Add shorthand -h for invoking help
    help_option_names=["-h", "--help"],
    # Give help some more room (default is 80)
    max_content_width=100,
    # Always show default values for options
    show_default=True,
    # Load command defaults from settings
    default_map=get_default_map(),
)


# Data object to add to Click context
class Context(t.NamedTuple):
    app: t.Optional[App]
    user: t.Optional[User] = None
    color: bool = False
    debug: bool = False
    quiet: bool = False


def pass_context(f: "t.Callable[te.Concatenate[Context, P], R]") -> "t.Callable[P, R]":
    """Pass `obj` from click context as first argument."""
    @wraps(f)
    def wrapped(*args: "P.args", **kwargs: "P.kwargs") -> R:
        ctx = click.get_current_context()
        return f(ctx.obj, *args, **kwargs)

    return wrapped


json_option = click.option(
    "--json",
    is_flag=True,
    default=False,
    help="Print data as JSON rather than human readable text"
)


@click.group(context_settings=CONTEXT)
@click.option("--debug/--no-debug", default=False, help="Log debug info to stderr")
@click.option("--color/--no-color", default=sys.stdout.isatty(), help="Use ANSI color in output")
@click.option("--quiet/--no-quiet", default=False, help="Don't print anything to stdout")
@click.version_option(__version__, message="%(prog)s v%(version)s")
@click.pass_context
def cli(
    ctx: click.Context,
    color: bool,
    debug: bool,
    quiet: bool,
    app: t.Optional[App] = None,
    user: t.Optional[User] = None,
):
    """Toot is a Mastodon CLI"""
    user, app = config.get_active_user_app()
    ctx.obj = Context(app, user, color, debug, quiet)
    ctx.color = color

    if debug:
        logging.basicConfig(level=logging.DEBUG)
