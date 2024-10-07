"""
Search endpoints
https://docs.joinmastodon.org/methods/search/
"""

from aiohttp import ClientResponse
from toot.async_http import request
from toot.cli import Context


async def search(ctx: Context, query: str) -> ClientResponse:
    """
    Perform a search
    https://docs.joinmastodon.org/methods/search/#v2
    """
    return await request(ctx, "GET", "/api/v2/search", params={
        "q": query,
        # "type": "hashtags"
    })
