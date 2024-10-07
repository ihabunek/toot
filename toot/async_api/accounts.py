"""
Accounts
https://docs.joinmastodon.org/methods/accounts/
"""
from typing import List, Optional
from aiohttp import ClientResponse
from toot.async_http import request
from toot.cli import AsyncContext
from toot.utils import drop_empty_values, str_bool

async def lookup(ctx: AsyncContext, acct: str) -> ClientResponse:
    """
    Look up an account by name and return its info.
    https://docs.joinmastodon.org/methods/accounts/#lookup
    """
    return await request(ctx, "GET", "/api/v1/accounts/lookup", params={"acct": acct})


async def relationships(ctx: AsyncContext, account_ids: List[str], *, with_suspended: bool) -> ClientResponse:
    """
    Check relationships to other accounts
    https://docs.joinmastodon.org/methods/accounts/#relationships
    """
    # TODO: verify this works with passing a list here, worked in httpx
    params = {"id[]": account_ids, "with_suspended": str_bool(with_suspended)}
    return await request(ctx, "GET", "/api/v1/accounts/relationships", params=params)


async def verify_credentials(ctx: AsyncContext) -> ClientResponse:
    """
    Test to make sure that the user token works.
    https://docs.joinmastodon.org/methods/accounts/#verify_credentials
    """
    return await request(ctx, "GET", "/api/v1/accounts/verify_credentials")


async def follow(
    ctx: AsyncContext,
    account_id: str, *,
    reblogs: Optional[bool] = None,
    notify: Optional[bool] = None,
) -> ClientResponse:
    """
    Follow the given account.
    Can also be used to update whether to show reblogs or enable notifications.
    https://docs.joinmastodon.org/methods/accounts/#follow
    """
    json = drop_empty_values({"reblogs": reblogs, "notify": notify})
    return await request(ctx, "POST", f"/api/v1/accounts/{account_id}/follow", json=json)


async def unfollow(ctx: AsyncContext, account_id: str) -> ClientResponse:
    """
    Unfollow the given account.
    https://docs.joinmastodon.org/methods/accounts/#unfollow
    """
    return await request(ctx, "POST", f"/api/v1/accounts/{account_id}/unfollow")


async def remove_from_followers(ctx: AsyncContext, account_id: str) -> ClientResponse:
    """
    Remove the given account from your followers.
    https://docs.joinmastodon.org/methods/accounts/#remove_from_followers
    """
    return await request(ctx, "POST", f"/api/v1/accounts/{account_id}/remove_from_followers")


async def block(ctx: AsyncContext, account_id: str) -> ClientResponse:
    """
    Block the given account.
    https://docs.joinmastodon.org/methods/accounts/#block
    """
    return await request(ctx, "POST", f"/api/v1/accounts/{account_id}/block")


async def unblock(ctx: AsyncContext, account_id: str) -> ClientResponse:
    """
    Unblock the given account.
    https://docs.joinmastodon.org/methods/accounts/#unblock
    """
    return await request(ctx, "POST", f"/api/v1/accounts/{account_id}/unblock")


async def mute(ctx: AsyncContext, account_id: str) -> ClientResponse:
    """
    Mute the given account.
    https://docs.joinmastodon.org/methods/accounts/#mute
    """
    return await request(ctx, "POST", f"/api/v1/accounts/{account_id}/mute")


async def unmute(ctx: AsyncContext, account_id: str) -> ClientResponse:
    """
    Unmute the given account.
    https://docs.joinmastodon.org/methods/accounts/#unmute
    """
    return await request(ctx, "POST", f"/api/v1/accounts/{account_id}/unmute")


async def pin(ctx: AsyncContext, account_id: str) -> ClientResponse:
    """
    Add the given account to the user’s featured profiles.
    https://docs.joinmastodon.org/methods/accounts/#pin
    """
    return await request(ctx, "POST", f"/api/v1/accounts/{account_id}/pin")


async def unpin(ctx: AsyncContext, account_id: str) -> ClientResponse:
    """
    Remove the given account from the user’s featured profiles.
    https://docs.joinmastodon.org/methods/accounts/#unpin
    """
    return await request(ctx, "POST", f"/api/v1/accounts/{account_id}/unpin")


async def note(ctx: AsyncContext, account_id: str, comment: str) -> ClientResponse:
    """
    Sets a private note on a user.
    https://docs.joinmastodon.org/methods/accounts/#note
    """
    return await request(ctx, "POST", f"/api/v1/accounts/{account_id}/note", json={"comment": comment})
