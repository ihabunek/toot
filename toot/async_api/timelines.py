"""
Timelines API
https://docs.joinmastodon.org/methods/timelines/
"""
import re

from typing import Mapping, Optional
from urllib.parse import quote, urlparse

from aiohttp import ClientSession

from toot import Context
from toot.ahttp import request
from toot.utils import str_bool
from toot.async_api.search import find_account


async def anon_public_timeline_generator(ctx, instance, local=False, limit=20):
    path = '/api/v1/timelines/public'
    params = {'local': str_bool(local), 'limit': limit}
    return _anon_timeline_generator(ctx, instance, path, params)


async def anon_tag_timeline_generator(ctx, instance, hashtag, local=False, limit=20):
    path = f"/api/v1/timelines/tag/{quote(hashtag)}"
    params = {'local': str_bool(local), 'limit': limit}
    return _anon_timeline_generator(ctx, instance, path, params)


async def home_timeline_generator(ctx: Context, limit=20):
    path = "/api/v1/timelines/home"
    params = {"limit": limit}
    return _timeline_generator(ctx, path, params)


async def public_timeline_generator(ctx: Context, local=False, limit=20):
    path = '/api/v1/timelines/public'
    params = {'local': str_bool(local), 'limit': limit}
    return _timeline_generator(ctx, path, params)


async def tag_timeline_generator(ctx: Context, hashtag, local=False, limit=20):
    path = f"/api/v1/timelines/tag/{quote(hashtag)}"
    params = {'local': str_bool(local), 'limit': limit}
    return _timeline_generator(ctx, path, params)


async def bookmark_timeline_generator(ctx: Context, limit=20):
    path = '/api/v1/bookmarks'
    params = {'limit': limit}
    return _timeline_generator(ctx, path, params)


async def notification_timeline_generator(ctx: Context, limit=20):
    # exclude all but mentions and statuses
    exclude_types = ["follow", "favourite", "reblog", "poll", "follow_request"]
    params = {"exclude_types[]": exclude_types, "limit": limit}
    return _notification_timeline_generator(ctx, "/api/v1/notifications", params)


async def conversation_timeline_generator(ctx: Context, limit=20):
    path = "/api/v1/conversations"
    params = {"limit": limit}
    return _conversation_timeline_generator(ctx, path, params)


async def account_timeline_generator(ctx: Context, account_name: str, replies=False, reblogs=False, limit=20):
    account = await find_account(ctx, account_name)
    path = f"/api/v1/accounts/{account['id']}/statuses"
    params = {"limit": limit, "exclude_replies": not replies, "exclude_reblogs": not reblogs}
    return _timeline_generator(ctx, path, params)


async def list_timeline_generator(ctx: Context, list_id: str, limit: int = 20):
    path = f"/api/v1/timelines/list/{list_id}"
    return _timeline_generator(ctx, path, {"limit": limit})


async def _anon_timeline_generator(ctx: Context, instance: str, path: Optional[str], params=None):
    # TODO: reuse anon session? remove base url from ctx.session?
    async with ClientSession() as session:
        ctx = Context(ctx.app, ctx.user, session)
        while path:
            response = await request(ctx, "GET", f"https://{instance}{path}", params=params)
            yield response.json
            path = _get_next_path(response.headers)


async def _timeline_generator(ctx: Context, path: Optional[str], params=None):
    while path:
        response = await request(ctx, "GET", path, params=params)
        yield response.json
        path = _get_next_path(response.headers)


async def _notification_timeline_generator(ctx: Context, path: Optional[str], params=None):
    while path:
        response = await request(ctx, "GET", path, params=params)
        yield [n["status"] for n in response.json if n["status"]]
        path = _get_next_path(response.headers)


async def _conversation_timeline_generator(ctx, path, params=None):
    while path:
        response = await request(ctx, "GET", path, params=params)
        yield [c["last_status"] for c in response.json if c["last_status"]]
        path = _get_next_path(response.headers)


def _get_next_path(headers: Mapping[str, str]) -> Optional[str]:
    """Given timeline response headers, returns the path to the next batch"""
    links = headers.get('Link', '')
    matches = re.match('<([^>]+)>; rel="next"', links)
    if matches:
        parsed = urlparse(matches.group(1))
        return "?".join([parsed.path, parsed.query])
