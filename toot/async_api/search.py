"""
Search
https://docs.joinmastodon.org/methods/search/
"""

from typing import Optional

from toot import Context
from toot.ahttp import request
from toot.exceptions import ConsoleError
from toot.utils import str_bool


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
