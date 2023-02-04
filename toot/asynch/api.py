import uuid

from toot import CLIENT_NAME, CLIENT_WEBSITE, config, App, User
from typing import Literal, List, Optional
from toot.asynch.http import request, Params, Response
from toot.utils import str_bool


# ------------------------------------------------------------------------------
# Types
# ------------------------------------------------------------------------------

Visibility = Literal["public", "unlisted", "private", "direct"]


# ------------------------------------------------------------------------------
# Accounts
# https://docs.joinmastodon.org/methods/accounts/
# ------------------------------------------------------------------------------

async def register_account(
    app: App,
    auth_token: str,
    username: str,
    email: str,
    password: str,
    locale: str = "en",
    agreement: bool = True
) -> Response:
    url = f"{app.base_url}/api/v1/accounts"
    headers = {"Authorization": f"Bearer {auth_token}"}

    json = {
        "username": username,
        "email": email,
        "password": password,
        "agreement": agreement,
        "locale": locale
    }

    return await request("POST", url, json=json, headers=headers)


async def verify_credentials(app, user):
    return await auth_get(app, user, "/api/v1/accounts/verify_credentials")


# ------------------------------------------------------------------------------
# Apps
# https://docs.joinmastodon.org/methods/apps/
# ------------------------------------------------------------------------------

async def create_app(domain: str, scheme: str = "https") -> Response:
    url = f"{scheme}://{domain}/api/v1/apps"

    json = {
        "client_name": CLIENT_NAME,
        "redirect_uris": "urn:ietf:wg:oauth:2.0:oob",
        "scopes": "read write follow",
        "website": CLIENT_WEBSITE,
    }

    return await request("POST", url, json=json)


# ------------------------------------------------------------------------------
# Instance
# https://docs.joinmastodon.org/methods/instance/
# ------------------------------------------------------------------------------

async def instance_v1(url: str) -> Response:
    return await request("GET", f"{url}/api/v1/instance")


async def instance_v2(url: str) -> Response:
    return await request("GET", f"{url}/api/v2/instance")


# ------------------------------------------------------------------------------
# Statuses
# https://docs.joinmastodon.org/methods/statuses/
# ------------------------------------------------------------------------------

async def post_status(
    app: App,
    user: User,
    status: str,
    visibility: Visibility = "public",
    media_ids: Optional[List[int]] = None,
    sensitive: bool = False,
    spoiler_text: Optional[str] = None,
    in_reply_to_id: Optional[int] = None,
    language: Optional[str] = None,
    scheduled_at: Optional[str] = None,
    content_type: Optional[str] = None,
) -> Response:
    """
    Posts a new status.
    https://github.com/tootsuite/documentation/blob/master/Using-the-API/API.md#posting-a-new-status
    """

    # Idempotency key assures the same status is not posted multiple times
    # if the request is retried.
    headers = {"Idempotency-Key": uuid.uuid4().hex}

    params = {
        "status": status,
        "media_ids[]": media_ids,
        "visibility": visibility,
        "sensitive": str_bool(sensitive),
        "spoiler_text": spoiler_text,
        "in_reply_to_id": in_reply_to_id,
        "language": language,
        "scheduled_at": scheduled_at
    }

    if content_type:
        params["content_type"] = content_type

    return await auth_request(app, user, "POST", "/api/v1/statuses", json=params, headers=headers)


async def get_status(app: App, user: User, id: int) -> Response:
    return await auth_request(app, user, "GET", f"/api/v1/statuses/{id}")


async def delete_status(app: App, user: User, id: int) -> Response:
    return await auth_request(app, user, "DELETE", f"/api/v1/statuses/{id}")


async def timeline(app: App, user: User) -> Response:
    return await auth_request(app, user, "GET", "/api/v1/timelines/home")


# ------------------------------------------------------------------------------
# OAuth
# https://docs.joinmastodon.org/methods/apps/oauth/
# ------------------------------------------------------------------------------

async def app_token(app):
    json = {
        "client_id": app.client_id,
        "client_secret": app.client_secret,
        "grant_type": "client_credentials",
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "scope": "read write"
    }

    return await request("POST", f"{app.base_url}/oauth/token", json=json)


# ------------------------------------------------------------------------------
# ???
# ------------------------------------------------------------------------------

async def search_accounts(app, user, query):
    return await auth_request(app, user, "GET", "/api/v1/accounts/search", params={"q": query})


# ------------------------------------------------------------------------------
# Common
# ------------------------------------------------------------------------------

async def anon_get(url: str, params: Optional[Params] = None):
    return await request("GET", url, params=params)


async def auth_get(app, user, path, params: Optional[Params] = None):
    url = app.base_url + path
    headers = {"Authorization": f"Bearer {user.access_token}"}
    return await request("GET", url, params=params, headers=headers)


async def auth_request(app, user, method, path, /, *, headers={}, **kwargs):
    url = app.base_url + path
    headers.update({"Authorization": f"Bearer {user.access_token}"})
    return await request(method, url, headers=headers, **kwargs)
