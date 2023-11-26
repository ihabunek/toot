import logging
import sys
import click

from functools import wraps
from toot import App, User, config
from typing import Callable, Concatenate, NamedTuple, Optional, ParamSpec, TypeVar


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
)


# Data object to add to Click context
class Context(NamedTuple):
    app: Optional[App] = None
    user: Optional[User] = None
    color: bool = False
    debug: bool = False
    quiet: bool = False


P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")


def pass_context(f: Callable[Concatenate[Context, P], R]) -> Callable[P, R]:
    """Pass `obj` from click context as first argument."""
    @wraps(f)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
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
@click.pass_context
def cli(ctx, color, debug, quiet, app=None, user=None):
    """Toot is a Mastodon CLI"""
    user, app = config.get_active_user_app()
    ctx.obj = Context(app, user, color, debug, quiet)

    if debug:
        logging.basicConfig(level=logging.DEBUG)
