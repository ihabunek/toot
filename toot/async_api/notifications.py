"""
Notifications API
https://docs.joinmastodon.org/methods/notifications/
"""
from aiohttp import ClientResponse

from toot.async_http import request
from toot.cli import Context


async def get(ctx: Context, notification_id: str) -> ClientResponse:
    """
    Fetch a single notification.
    https://docs.joinmastodon.org/methods/notifications/#get-one
    """
    return await request(ctx, "GET", f"/api/v1/notifications/{notification_id}")
