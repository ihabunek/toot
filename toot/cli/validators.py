import click
import re


def validate_language(ctx, param, value):
    if value is None:
        return None

    value = value.strip().lower()
    if re.match(r"^[a-z]{2}$", value):
        return value

    raise click.BadParameter("Language should be a two letter abbreviation.")


def validate_duration(ctx, param, value: str) -> int:
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
