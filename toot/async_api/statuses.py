"""
Statuses API
https://docs.joinmastodon.org/methods/statuses/
"""
from typing import Any, Dict, List, Optional
from aiohttp import ClientResponse
from uuid import uuid4

from toot.async_http import request
from toot.cli import Context


async def get(ctx: Context, status_id: str)-> ClientResponse:
    """
    Fetch a single status.
    https://docs.joinmastodon.org/methods/statuses/#get
    """
    return await request(ctx, "GET", f"/api/v1/statuses/{status_id}")


async def context(ctx: Context, status_id: str)-> ClientResponse:
    """
    View statuses above and below this status in the thread.
    https://docs.joinmastodon.org/methods/statuses/#context
    """
    return await request(ctx, "GET", f"/api/v1/statuses/{status_id}/context")


async def post(
    ctx: Context,
    status: str,
    visibility: str = "public",
    sensitive: bool = False,
    spoiler_text: Optional[str] = None,
    in_reply_to: Optional[str] = None,
    local_only: Optional[bool] = None,
    media_ids: Optional[List[str]] = None,
)-> ClientResponse:
    # Idempotency key assures the same status is not posted multiple times
    # if the request is retried.
    headers = {"Idempotency-Key": uuid4().hex}

    payload = drop_empty_values({
        "status": status,
        "visibility": visibility,
        "sensitive": sensitive,
        "spoiler_text": spoiler_text,
        "in_reply_to_id": in_reply_to,
        "local_only": local_only,
        "media_ids": media_ids,
    })

    return await request(ctx, "POST", "/api/v1/statuses", headers=headers, json=payload)


async def edit(
    ctx: Context,
    status_id: str,
    status: str,
    visibility: str = "public",
    sensitive: bool = False,
    spoiler_text: Optional[str] = None,
    media_ids: Optional[List[str]] = None,
)-> ClientResponse:
    """
    Edit an existing status.
    https://docs.joinmastodon.org/methods/statuses/#edit
    """

    payload = drop_empty_values({
        "status": status,
        "visibility": visibility,
        "sensitive": sensitive,
        "spoiler_text": spoiler_text,
        "media_ids": media_ids,
    })

    return await request(ctx, "PUT", f"/api/v1/statuses/{status_id}", json=payload)


async def delete(ctx: Context, status_id: str)-> ClientResponse:
    return await request(ctx, "DELETE", f"/api/v1/statuses/{status_id}")


def drop_empty_values(data: Dict[Any, Any]) -> Dict[Any, Any]:
    """Remove keys whose values are null"""
    return {k: v for k, v in data.items() if v is not None}


async def source(ctx: Context, status_id: str):
    """
    Fetch the original plaintext source for a status. Only works on locally-posted statuses.
    https://docs.joinmastodon.org/methods/statuses/#source
    """
    path = f"/api/v1/statuses/{status_id}/source"
    return await request(ctx, "GET", path)


async def favourite(ctx: Context, status_id: str):
    """
    Add a status to your favourites list.
    https://docs.joinmastodon.org/methods/statuses/#favourite
    """
    path = f"/api/v1/statuses/{status_id}/favourite"
    return await request(ctx, "POST", path)


async def unfavourite(ctx: Context, status_id: str):
    """
    Remove a status from your favourites list.
    https://docs.joinmastodon.org/methods/statuses/#unfavourite
    """
    path = f"/api/v1/statuses/{status_id}/unfavourite"
    return await request(ctx, "POST", path)


async def boost(ctx: Context, status_id: str):
    """
    Reshare a status on your own profile.
    https://docs.joinmastodon.org/methods/statuses/#boost
    """
    path = f"/api/v1/statuses/{status_id}/reblog"
    return await request(ctx, "POST", path)


async def unboost(ctx: Context, status_id: str):
    """
    Undo a reshare of a status.
    https://docs.joinmastodon.org/methods/statuses/#unreblog
    """
    path = f"/api/v1/statuses/{status_id}/unreblog"
    return await request(ctx, "POST", path)
