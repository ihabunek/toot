from functools import wraps
from typing import Iterable, List, Optional, Tuple
from urllib.parse import quote

import click
from requests import Response

from toot import api, http
from toot.cli import Context, cli, json_option, pass_context
from toot.cli.lists import get_list_id
from toot.cli.validators import validate_instance
from toot.entities import (
    Account,
    Status,
    from_dict_list,
    from_response,
    from_response_list,
)
from toot.output import get_continue, get_max_width, get_terminal_height, print_timeline, status_lines
from toot.utils import drop_empty_values, str_bool_nullable


def common_timeline_options(func):
    @click.option(
        "--min-id",
        help="""All results returned will be lesser than this ID. In effect,
             sets an upper bound on results.""",
    )
    @click.option(
        "--max-id",
        help="""All results returned will be greater than this ID. In effect,
             sets a lower bound on results.""",
    )
    @click.option(
        "--since-id",
        help="""Returns results immediately newer than this ID. In effect,
             sets a cursor at this ID and paginates forward.""",
    )
    @click.option(
        "-l",
        "--limit",
        type=int,
        help="""Number of results to fetch per request. [default: 20] [max: 40].
             (limit and max may depend on your server)""",
    )
    @click.option(
        "-p/ ",
        "--pager/--no-pager",
        help="Page the results",
        default=True,
    )
    @click.option(
        "-c",
        "--clear/--no-clear",
        help="Clear the screen before printing. If paged, clear before each page.",
        default=True,
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


instance_option = click.option(
    "-i",
    "--instance",
    callback=validate_instance,
    help="""Domain or base URL of the instance, e.g. 'mastodon.social' or
         'https://mastodon.social'. If not given will display timeline of the
         logged in server.""",
)


@cli.group()
def timelines():
    """Show various timelines"""


@timelines.command()
@click.argument("account_name")
@common_timeline_options
@json_option
@pass_context
def account(
    ctx: Context,
    account_name: str,
    min_id: Optional[str],
    max_id: Optional[str],
    since_id: Optional[str],
    limit: Optional[int],
    pager: bool,
    clear: bool,
    json: bool,
):
    """View statuses posted to the given account."""
    response = api.lookup(ctx.app, ctx.user, account_name)
    account = from_response(Account, response)
    path = f"/api/v1/accounts/{account.id}/statuses"
    params = {
        "min_id": min_id,
        "max_id": max_id,
        "since_id": since_id,
        "limit": limit,
    }

    _show_timeline(ctx, path, params, json, pager, clear, limit)


@timelines.command()
@common_timeline_options
@json_option
@pass_context
def home(
    ctx: Context,
    min_id: Optional[str],
    max_id: Optional[str],
    since_id: Optional[str],
    limit: Optional[int],
    pager: bool,
    clear: bool,
    json: bool,
):
    """View statuses from followed users and hashtags."""
    path = "/api/v1/timelines/home"
    params = {
        "min_id": min_id,
        "max_id": max_id,
        "since_id": since_id,
        "limit": limit,
    }

    _show_timeline(ctx, path, params, json, pager, clear, limit)


@timelines.command()
@click.argument("link_url")
@common_timeline_options
@json_option
@pass_context
def link(
    ctx: Context,
    link_url: str,
    min_id: Optional[str],
    max_id: Optional[str],
    since_id: Optional[str],
    limit: Optional[int],
    pager: bool,
    clear: bool,
    json: bool,
):
    """View statuses sharing a link.

    View public statuses containing a link to the specified
    currently-trending article. This only lists statuses from people who have
    opted in to discoverability features."""
    path = "/api/v1/timelines/link"

    params = {
        "url": link_url,
        "min_id": min_id,
        "max_id": max_id,
        "since_id": since_id,
        "limit": limit,
    }

    _show_timeline(ctx, path, params, json, pager, clear, limit)


@timelines.command("list")
@click.argument("list_name_or_id")
@common_timeline_options
@json_option
@pass_context
def list_cmd(
    ctx: Context,
    list_name_or_id: str,
    min_id: Optional[str],
    max_id: Optional[str],
    since_id: Optional[str],
    limit: Optional[int],
    pager: bool,
    clear: bool,
    json: bool,
):
    """View statuses in the given list timeline."""
    list_id = get_list_id(ctx, list_name_or_id, list_name_or_id)
    path = f"/api/v1/timelines/list/{list_id}"

    params = {
        "min_id": min_id,
        "max_id": max_id,
        "since_id": since_id,
        "limit": limit,
    }

    _show_timeline(ctx, path, params, json, pager, clear, limit)


@timelines.command()
@common_timeline_options
@instance_option
@click.option(
    "--local",
    is_flag=True,
    default=None,
    help="Show only local statuses",
)
@click.option(
    "--remote",
    is_flag=True,
    default=None,
    help="Show only remote statuses",
)
@click.option(
    "--only-media",
    is_flag=True,
    default=None,
    help="Show only statuses with media attached",
)
@json_option
@pass_context
def public(
    ctx: Context,
    instance: Optional[str],
    min_id: Optional[str],
    max_id: Optional[str],
    since_id: Optional[str],
    limit: Optional[int],
    pager: bool,
    clear: bool,
    local: Optional[bool],
    remote: Optional[bool],
    only_media: Optional[bool],
    json: bool,
):
    """View public statuses."""
    path = "/api/v1/timelines/public"
    params = {
        "min_id": min_id,
        "max_id": max_id,
        "since_id": since_id,
        "limit": limit,
        "local": str_bool_nullable(local),
        "remote": str_bool_nullable(remote),
        "only_media": str_bool_nullable(only_media),
    }

    if instance:
        url = f"{instance}{path}"
        _show_anon_timeline(url, params, json, pager, clear, limit)
    else:
        _show_timeline(ctx, path, params, json, pager, clear, limit)


@timelines.command()
@common_timeline_options
@instance_option
@click.argument("tag_name")
@click.option(
    "--local",
    is_flag=True,
    default=None,
    help="Show only local statuses",
)
@click.option(
    "--remote",
    is_flag=True,
    default=None,
    help="Show only remote statuses",
)
@click.option(
    "--only-media",
    is_flag=True,
    default=None,
    help="Show only statuses with media attached",
)
@click.option(
    "--any",
    multiple=True,
    help="Return statuses that contain any of these additional tags (can be specified multiple times)",
)
@click.option(
    "--all",
    multiple=True,
    help="Return statuses that contain all of these additional tags (can be specified multiple times)",
)
@click.option(
    "--none",
    multiple=True,
    help="Return statuses that contain none of these additional tags (can be specified multiple times)",
)
@json_option
@pass_context
def tag(
    ctx: Context,
    tag_name: str,
    instance: Optional[str],
    min_id: Optional[str],
    max_id: Optional[str],
    since_id: Optional[str],
    limit: Optional[int],
    pager: bool,
    clear: bool,
    local: Optional[bool],
    remote: Optional[bool],
    only_media: Optional[bool],
    any: Tuple[str],
    all: Tuple[str],
    none: Tuple[str],
    json: bool,
):
    """View public statuses containing the given hashtag."""
    path = f"/api/v1/timelines/tag/{quote(tag_name)}"
    params = {
        "min_id": min_id,
        "max_id": max_id,
        "since_id": since_id,
        "limit": limit,
        "local": str_bool_nullable(local),
        "remote": str_bool_nullable(remote),
        "only_media": str_bool_nullable(only_media),
        "any[]": any or None,
        "all[]": all or None,
        "none[]": none or None,
    }

    if instance:
        url = f"{instance}{path}"
        _show_anon_timeline(url, params, json, pager, clear, limit)
    else:
        _show_timeline(ctx, path, params, json, pager, clear, limit)


def _show_timeline(ctx, path, params, json, pager, clear, limit):
    params = drop_empty_values(params)

    if json:
        response = http.get(ctx.app, ctx.user, path, params)
        click.echo(response.text)
        return

    if pager:
        responses = http.get_paged(ctx.app, ctx.user, path, params)
        _print_paged(responses, clear)
        return

    response = http.get(ctx.app, ctx.user, path, params)
    _print_single(response, clear, limit)


def _show_anon_timeline(url, params, json, pager, clear, limit):
    params = drop_empty_values(params)

    if json:
        response = http.anon_get(url, params)
        click.echo(response.text)
        return

    if pager:
        responses = http.anon_get_paged(url, params)
        _print_paged(responses, clear)
        return

    response = http.anon_get(url, params)
    _print_single(response, clear, limit)


def _print_single(response: Response, clear: bool, limit: Optional[int]):
    statuses = from_response_list(Status, response)
    if clear:
        click.clear()
    if statuses:
        print_timeline(statuses)
        if not limit or len(statuses) == limit:
            click.secho(
                "There may be more results. Increase the --limit or use --pager to see the rest.",
                dim=True,
            )
    else:
        click.echo("No statuses found")


def _print_paged(responses: Iterable[Response], clear: bool):
    width = get_max_width()
    height = get_terminal_height()
    separator = "─" * width

    def _page_generator():
        batch_lines: List[str] = []
        for response in responses:
            statuses = from_dict_list(Status, response.json())
            for status in statuses:
                lines = [separator] + list(status_lines(status))
                if len(batch_lines) + len(lines) > height - 2 and batch_lines:
                    yield "\n".join(batch_lines) + "\n" + separator
                    batch_lines = []
                batch_lines.extend(lines)

        if batch_lines:
            yield "\n".join(batch_lines) + "\n" + separator

    first = True
    printed_any = False
    for page in _page_generator():
        if not first and not get_continue():
            break
        if clear:
            click.clear()
        click.echo(page)
        first = False
        printed_any = True

    if not printed_any:
        click.echo("No statuses found")
