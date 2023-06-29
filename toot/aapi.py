import re
from typing import Optional
from urllib.parse import urlparse
from uuid import uuid4

from toot import Context
from toot.ahttp import Response, request
from toot.exceptions import ConsoleError
from toot.utils import drop_empty_values, str_bool


async def find_account(ctx: Context, account_name: str):
    if not account_name:
        raise ConsoleError("Empty account name given")

    normalized_name = account_name.lstrip("@").lower()

    # Strip @<instance_name> from accounts on the local instance. The `acct`
    # field in account object contains the qualified name for users of other
    # instances, but only the username for users of the local instance. This is
    # required in order to match the account name below.
    if "@" in normalized_name:
        [username, instance] = normalized_name.split("@", maxsplit=1)
        if instance == ctx.app.instance:
            normalized_name = username

    response = await search(ctx, account_name, type="accounts", resolve=True)
    accounts = response.json["accounts"]

    for account in accounts:
        if account["acct"].lower() == normalized_name:
            return account

    raise ConsoleError("Account not found")


# ------------------------------------------------------------------------------
# Accounts
# https://docs.joinmastodon.org/methods/accounts/
# ------------------------------------------------------------------------------


async def verify_credentials(ctx: Context) -> Response:
    """
    Test to make sure that the user token works.
    https://docs.joinmastodon.org/methods/accounts/#verify_credentials
    """
    return await request(ctx, "GET", "/api/v1/accounts/verify_credentials")


# ------------------------------------------------------------------------------
# Search
# https://docs.joinmastodon.org/methods/search/
# ------------------------------------------------------------------------------

async def search(ctx: Context, query: str, resolve: bool = False, type: Optional[str] = None):
    """
    Perform a search.
    https://docs.joinmastodon.org/methods/search/#v2
    """
    return await request(ctx, "GET", "/api/v2/search", params={
        "q": query,
        "resolve": str_bool(resolve),
        "type": type
    })

# ------------------------------------------------------------------------------
# Statuses
# https://docs.joinmastodon.org/methods/statuses/
# ------------------------------------------------------------------------------


async def post_status(
    ctx: Context,
    status,
    visibility='public',
    media_ids=None,
    sensitive=False,
    spoiler_text=None,
    in_reply_to_id=None,
    language=None,
    scheduled_at=None,
    content_type=None,
    poll_options=None,
    poll_expires_in=None,
    poll_multiple=None,
    poll_hide_totals=None,
):
    """
    Publish a new status.
    https://docs.joinmastodon.org/methods/statuses/#create
    """

    # Idempotency key assures the same status is not posted multiple times
    # if the request is retried.
    headers = {"Idempotency-Key": uuid4().hex}

    # Strip keys for which value is None
    # Sending null values doesn't bother Mastodon, but it breaks Pleroma
    data = drop_empty_values({
        "status": status,
        "media_ids": media_ids,
        "visibility": visibility,
        "sensitive": sensitive,
        "in_reply_to_id": in_reply_to_id,
        "language": language,
        "scheduled_at": scheduled_at,
        "content_type": content_type,
        "spoiler_text": spoiler_text,
    })

    if poll_options:
        data["poll"] = {
            "options": poll_options,
            "expires_in": poll_expires_in,
            "multiple": poll_multiple,
            "hide_totals": poll_hide_totals,
        }

    return await request(ctx, "POST", "/api/v1/statuses", json=data, headers=headers)


async def get_status(ctx: Context, status_id) -> Response:
    url = f"/api/v1/statuses/{status_id}"
    return await request(ctx, "GET", url)


async def get_status_context(ctx: Context, status_id) -> Response:
    url = f"/api/v1/statuses/{status_id}/context"
    return await request(ctx, "GET", url)


# Timelines

async def home_timeline_generator(ctx: Context, limit=20):
    path = "/api/v1/timelines/home"
    params = {"limit": limit}
    return _timeline_generator(ctx, path, params)


async def _timeline_generator(ctx: Context, path: str, params=None):
    while path:
        response = await request(ctx, "GET", path, params=params)
        yield response.json
        path = _get_next_path(response.headers)


def _get_next_path(headers: dict):
    """Given timeline response headers, returns the path to the next batch"""
    links = headers.get('Link', '')
    matches = re.match('<([^>]+)>; rel="next"', links)
    if matches:
        parsed = urlparse(matches.group(1))
        return "?".join([parsed.path, parsed.query])
