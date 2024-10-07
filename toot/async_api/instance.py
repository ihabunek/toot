"""
Accounts
https://docs.joinmastodon.org/methods/instance/
"""
from aiohttp import ClientResponse

from toot.async_http import request
from toot.cli import Context


async def server_information(ctx: Context) -> ClientResponse:
    """
    Obtain general information about the server.
    https://docs.joinmastodon.org/methods/instance/#v1
    """
    return await request(ctx, "GET", "/api/v1/instance")


async def server_information_v2(ctx: Context) -> ClientResponse:
    """
    Obtain general information about the server.
    https://docs.joinmastodon.org/methods/instance/#v2
    """
    return await request(ctx, "GET", "/api/v2/instance")


async def extended_description(ctx: Context) -> ClientResponse:
    """
    Obtain an extended description of this server
    https://docs.joinmastodon.org/methods/instance/#extended_description
    """
    return await request(ctx, "GET", "/api/v1/instance/extended_description")


async def user_preferences(ctx: Context) -> ClientResponse:
    """
    Fetch the user's server-side preferences for this instance.
    https://docs.joinmastodon.org/methods/preferences/
    """
    return await request(ctx, "GET", "/api/v1/preferences")
