import click
import re

from click import Context
from typing import Optional

from toot.cli import TUI_COLORS


def validate_language(ctx: Context, param: str, value: Optional[str]):
    if value is None:
        return None

    value = value.strip().lower()
    if re.match(r"^[a-z]{2}$", value):
        return value

    raise click.BadParameter("Language should be a two letter abbreviation.")


def validate_duration(ctx: Context, param: str, value: Optional[str]) -> Optional[int]:
    if value is None:
        return None

    match = re.match(r"""^
        (([0-9]+)\s*(days|day|d))?\s*
        (([0-9]+)\s*(hours|hour|h))?\s*
        (([0-9]+)\s*(minutes|minute|m))?\s*
        (([0-9]+)\s*(seconds|second|s))?\s*
    $""", value, re.X)

    if not match:
        raise click.BadParameter(f"Invalid duration: {value}")

    days = match.group(2)
    hours = match.group(5)
    minutes = match.group(8)
    seconds = match.group(11)

    days = int(match.group(2) or 0) * 60 * 60 * 24
    hours = int(match.group(5) or 0) * 60 * 60
    minutes = int(match.group(8) or 0) * 60
    seconds = int(match.group(11) or 0)

    duration = days + hours + minutes + seconds

    if duration == 0:
        raise click.BadParameter("Empty duration")

    return duration


def validate_instance(ctx: click.Context, param: str, value: Optional[str]):
    """
    Instance can be given either as a base URL or the domain name.
    Return the base URL.
    """
    if not value:
        return None

    value = value.rstrip("/")
    return value if value.startswith("http") else f"https://{value}"


def validate_tui_colors(ctx, param, value) -> Optional[int]:
    if value is None:
        return None

    if value in TUI_COLORS.values():
        return value

    if value in TUI_COLORS.keys():
        return TUI_COLORS[value]

    raise click.BadParameter(f"Invalid value: {value}. Expected one of: {', '.join(TUI_COLORS)}")


def validate_cache_size(ctx: click.Context, param: str, value: Optional[str]) -> Optional[int]:
    """validates the cache size parameter"""

    if value is None:
        return 1024 * 1024 * 10  # default 10MB
    else:
        if value.isdigit():
            size = int(value)
        else:
            raise click.BadParameter("Cache size must be numeric.")

    if size > 1024:
        raise click.BadParameter("Cache size too large: 1024MB maximum.")
    elif size < 1:
        raise click.BadParameter("Cache size too small: 1MB minimum.")
    return size


def validate_positive(_ctx: click.Context, _param: click.Parameter, value: Optional[int]):
    if value is not None and value <= 0:
        raise click.BadParameter("must be greater than 0")
    return value
