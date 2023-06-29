"""
Statuses
https://docs.joinmastodon.org/methods/statuses/
"""

from uuid import uuid4

from toot import Context
from toot.ahttp import Response, request
from toot.utils import drop_empty_values


async def post(
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


async def get_context(ctx: Context, status_id) -> Response:
    url = f"/api/v1/statuses/{status_id}/context"
    return await request(ctx, "GET", url)
