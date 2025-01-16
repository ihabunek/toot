import mimetypes
import re
import uuid

from os import path
from requests import Response
from typing import BinaryIO, List, Optional
from urllib.parse import urlparse, urlencode, quote

from toot import App, User, http, CLIENT_NAME, CLIENT_WEBSITE
from toot.exceptions import ConsoleError
from toot.utils import drop_empty_values, str_bool, str_bool_nullable


SCOPES = 'read write follow'


def find_account(app, user, account_name):
    if not account_name:
        raise ConsoleError("Empty account name given")

    normalized_name = account_name.lstrip("@").lower()

    # Strip @<instance_name> from accounts on the local instance. The `acct`
    # field in account object contains the qualified name for users of other
    # instances, but only the username for users of the local instance. This is
    # required in order to match the account name below.
    if "@" in normalized_name:
        [username, instance] = normalized_name.split("@", maxsplit=1)
        if instance == app.instance:
            normalized_name = username

    response = search(app, user, account_name, type="accounts", resolve=True)
    for account in response.json()["accounts"]:
        if account["acct"].lower() == normalized_name:
            return account

    raise ConsoleError("Account not found")


def lookup(app, user, acct):
    return http.get(app, user, "/api/v1/accounts/lookup", {"acct": acct})


def _account_action(app, user, account, action) -> Response:
    url = f"/api/v1/accounts/{account}/{action}"
    return http.post(app, user, url)


def _status_action(app, user, status_id, action, data=None) -> Response:
    status_id = _resolve_status_id(app, user, status_id)
    url = f"/api/v1/statuses/{status_id}/{action}"
    return http.post(app, user, url, data=data)


def _resolve_status_id(app, user, id_or_url) -> str:
    """
    If given an URL instead of status ID, attempt to resolve the status ID.

    TODO: Not 100% sure this is the correct way of doing this, but it seems to
    work for all test cases I've thrown at it. So leaving it undocumented until
    we're happy it works.
    """
    if re.match(r"^https?://", id_or_url):
        response = search(app, user, id_or_url, resolve=True, type="statuses")
        statuses = response.json().get("statuses")

        if not statuses:
            raise ConsoleError(f"Cannot find status matching URL {id_or_url}")

        if len(statuses) > 1:
            raise ConsoleError(f"Found multiple statuses mathcing URL {id_or_url}")

        return statuses[0]["id"]

    return id_or_url


def _tag_action(app, user, tag_name, action) -> Response:
    url = f"/api/v1/tags/{tag_name}/{action}"
    return http.post(app, user, url)


def create_app(base_url):
    url = f"{base_url}/api/v1/apps"

    json = {
        'client_name': CLIENT_NAME,
        'redirect_uris': 'urn:ietf:wg:oauth:2.0:oob',
        'scopes': SCOPES,
        'website': CLIENT_WEBSITE,
    }

    return http.anon_post(url, json=json).json()


def get_muted_accounts(app, user):
    return http.get(app, user, "/api/v1/mutes").json()


def get_blocked_accounts(app, user):
    return http.get(app, user, "/api/v1/blocks").json()


def register_account(app, username, email, password, locale="en", agreement=True):
    """
    Register an account
    https://docs.joinmastodon.org/methods/accounts/#create
    """
    token = fetch_app_token(app)["access_token"]
    url = f"{app.base_url}/api/v1/accounts"
    headers = {"Authorization": f"Bearer {token}"}

    json = {
        "username": username,
        "email": email,
        "password": password,
        "agreement": agreement,
        "locale": locale
    }

    return http.anon_post(url, json=json, headers=headers).json()


def update_account(
    app,
    user,
    display_name=None,
    note=None,
    avatar=None,
    header=None,
    bot=None,
    discoverable=None,
    locked=None,
    privacy=None,
    sensitive=None,
    language=None
):
    """
    Update account credentials
    https://docs.joinmastodon.org/methods/accounts/#update_credentials
    """
    files = drop_empty_values({"avatar": avatar, "header": header})

    data = drop_empty_values({
        "bot": str_bool_nullable(bot),
        "discoverable": str_bool_nullable(discoverable),
        "display_name": display_name,
        "locked": str_bool_nullable(locked),
        "note": note,
        "source[language]": language,
        "source[privacy]": privacy,
        "source[sensitive]": str_bool_nullable(sensitive),
    })

    return http.patch(app, user, "/api/v1/accounts/update_credentials", files=files, data=data)


def fetch_app_token(app):
    json = {
        "client_id": app.client_id,
        "client_secret": app.client_secret,
        "grant_type": "client_credentials",
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "scope": "read write"
    }

    return http.anon_post(f"{app.base_url}/oauth/token", json=json).json()


def login(app: App, username: str, password: str):
    url = app.base_url + '/oauth/token'

    data = {
        'grant_type': 'password',
        'client_id': app.client_id,
        'client_secret': app.client_secret,
        'username': username,
        'password': password,
        'scope': SCOPES,
    }

    return http.anon_post(url, data=data).json()


def get_browser_login_url(app: App) -> str:
    """Returns the URL for manual log in via browser"""
    return "{}/oauth/authorize/?{}".format(app.base_url, urlencode({
        "response_type": "code",
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "scope": SCOPES,
        "client_id": app.client_id,
    }))


def request_access_token(app: App, authorization_code: str):
    url = app.base_url + '/oauth/token'

    data = {
        'grant_type': 'authorization_code',
        'client_id': app.client_id,
        'client_secret': app.client_secret,
        'code': authorization_code,
        'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
    }

    return http.anon_post(url, data=data, allow_redirects=False).json()


def post_status(
    app,
    user,
    status,
    visibility=None,
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
) -> Response:
    """
    Publish a new status.
    https://docs.joinmastodon.org/methods/statuses/#create
    """

    # Idempotency key assures the same status is not posted multiple times
    # if the request is retried.
    headers = {"Idempotency-Key": uuid.uuid4().hex}

    # Strip keys for which value is None
    # Sending null values doesn't bother Mastodon, but it breaks Pleroma
    data = drop_empty_values({
        'status': status,
        'media_ids': media_ids,
        'visibility': visibility,
        'sensitive': sensitive,
        'in_reply_to_id': in_reply_to_id,
        'language': language,
        'scheduled_at': scheduled_at,
        'content_type': content_type,
        'spoiler_text': spoiler_text,
    })

    if poll_options:
        data["poll"] = {
            "options": poll_options,
            "expires_in": poll_expires_in,
            "multiple": poll_multiple,
            "hide_totals": poll_hide_totals,
        }

    return http.post(app, user, '/api/v1/statuses', json=data, headers=headers)


def edit_status(
    app,
    user,
    id,
    status,
    visibility='public',
    media_ids=None,
    sensitive=False,
    spoiler_text=None,
    in_reply_to_id=None,
    language=None,
    content_type=None,
    poll_options=None,
    poll_expires_in=None,
    poll_multiple=None,
    poll_hide_totals=None,
) -> Response:
    """
    Edit an existing status
    https://docs.joinmastodon.org/methods/statuses/#edit
    """

    # Strip keys for which value is None
    # Sending null values doesn't bother Mastodon, but it breaks Pleroma
    data = drop_empty_values({
        'status': status,
        'media_ids': media_ids,
        'visibility': visibility,
        'sensitive': sensitive,
        'in_reply_to_id': in_reply_to_id,
        'language': language,
        'content_type': content_type,
        'spoiler_text': spoiler_text,
    })

    if poll_options:
        data["poll"] = {
            "options": poll_options,
            "expires_in": poll_expires_in,
            "multiple": poll_multiple,
            "hide_totals": poll_hide_totals,
        }

    return http.put(app, user, f"/api/v1/statuses/{id}", json=data)


def fetch_status(app, user, id):
    """
    Fetch a single status
    https://docs.joinmastodon.org/methods/statuses/#get
    """
    return http.get(app, user, f"/api/v1/statuses/{id}")


def fetch_status_source(app, user, id):
    """
    Fetch the source (original text) for a single status.
    This only works on local toots.
    https://docs.joinmastodon.org/methods/statuses/#source
    """
    return http.get(app, user, f"/api/v1/statuses/{id}/source")


def scheduled_statuses(app, user):
    """
    List scheduled statuses
    https://docs.joinmastodon.org/methods/scheduled_statuses/#get
    """
    return http.get(app, user, "/api/v1/scheduled_statuses").json()


def delete_status(app, user, status_id):
    """
    Deletes a status with given ID.
    https://github.com/tootsuite/documentation/blob/master/Using-the-API/API.md#deleting-a-status
    """
    return http.delete(app, user, f"/api/v1/statuses/{status_id}")


def favourite(app, user, status_id):
    return _status_action(app, user, status_id, 'favourite')


def unfavourite(app, user, status_id):
    return _status_action(app, user, status_id, 'unfavourite')


def reblog(app, user, status_id, visibility="public"):
    return _status_action(app, user, status_id, 'reblog', data={"visibility": visibility})


def unreblog(app, user, status_id):
    return _status_action(app, user, status_id, 'unreblog')


def pin(app, user, status_id):
    return _status_action(app, user, status_id, 'pin')


def unpin(app, user, status_id):
    return _status_action(app, user, status_id, 'unpin')


def bookmark(app, user, status_id):
    return _status_action(app, user, status_id, 'bookmark')


def unbookmark(app, user, status_id):
    return _status_action(app, user, status_id, 'unbookmark')


def translate(app, user, status_id):
    return _status_action(app, user, status_id, 'translate')


def context(app, user, status_id) -> Response:
    url = f"/api/v1/statuses/{status_id}/context"
    return http.get(app, user, url)


def reblogged_by(app, user, status_id) -> Response:
    url = f"/api/v1/statuses/{status_id}/reblogged_by"
    return http.get(app, user, url)


def get_timeline_generator(
    app: Optional[App],
    user: Optional[User],
    account: Optional[str] = None,
    list_id: Optional[str] = None,
    tag: Optional[str] = None,
    local: bool = False,
    public: bool = False,
    limit: int = 20,  # TODO
):
    if public:
        return public_timeline_generator(app, user, local=local, limit=limit)
    elif tag:
        return tag_timeline_generator(app, user, tag, local=local, limit=limit)
    elif account:
        return account_timeline_generator(app, user, account, limit=limit)
    elif list_id:
        return timeline_list_generator(app, user, list_id, limit=limit)
    else:
        return home_timeline_generator(app, user, limit=limit)


def _get_next_path(headers):
    """Given timeline response headers, returns the path to the next batch"""
    links = headers.get('Link', '')
    matches = re.match('<([^>]+)>; rel="next"', links)
    if matches:
        parsed = urlparse(matches.group(1))
        return "?".join([parsed.path, parsed.query])


def _get_next_url(headers) -> Optional[str]:
    """Given timeline response headers, returns the url to the next batch"""
    links = headers.get('Link', '')
    match = re.match('<([^>]+)>; rel="next"', links)
    if match:
        return match.group(1)


def _timeline_generator(app, user, path, params=None):
    if params:
        path += f"?{urlencode(params)}"

    while path:
        response = http.get(app, user, path)
        yield response.json()
        path = _get_next_path(response.headers)


def _notification_timeline_generator(app, user, path, params=None):
    for batch in _timeline_generator(app, user, path, params):
        yield [n["status"] for n in batch if n.get("status")]


def _conversation_timeline_generator(app, user, path, params=None):
    for batch in _timeline_generator(app, user, path, params):
        yield [c["last_status"] for c in batch if c.get("last_status")]


def home_timeline_generator(app, user, limit=20):
    path = "/api/v1/timelines/home"
    params = {"limit": limit}
    return _timeline_generator(app, user, path, params)


def public_timeline_generator(app, user, local=False, limit=20):
    path = '/api/v1/timelines/public'
    params = {'local': str_bool(local), 'limit': limit}
    return _timeline_generator(app, user, path, params)


def tag_timeline_generator(app, user, hashtag, local=False, limit=20):
    path = f"/api/v1/timelines/tag/{quote(hashtag)}"
    params = {'local': str_bool(local), 'limit': limit}
    return _timeline_generator(app, user, path, params)


def bookmark_timeline_generator(app, user, limit=20):
    path = '/api/v1/bookmarks'
    params = {'limit': limit}
    return _timeline_generator(app, user, path, params)


def notification_timeline_generator(app, user, limit=20):
    # exclude all but mentions and statuses
    exclude_types = ["follow", "favourite", "reblog", "poll", "follow_request"]
    params = {"exclude_types[]": exclude_types, "limit": limit}
    return _notification_timeline_generator(app, user, "/api/v1/notifications", params)


def conversation_timeline_generator(app, user, limit=20):
    path = "/api/v1/conversations"
    params = {"limit": limit}
    return _conversation_timeline_generator(app, user, path, params)


def account_timeline_generator(app, user, account_name: str, replies=False, reblogs=False, limit=20):
    account = find_account(app, user, account_name)
    path = f"/api/v1/accounts/{account['id']}/statuses"
    params = {"limit": limit, "exclude_replies": not replies, "exclude_reblogs": not reblogs}
    return _timeline_generator(app, user, path, params)


def timeline_list_generator(app, user, list_id, limit=20):
    path = f"/api/v1/timelines/list/{list_id}"
    return _timeline_generator(app, user, path, {'limit': limit})


def _anon_timeline_generator(url, params=None):
    if params:
        url += f"?{urlencode(params)}"

    while url:
        response = http.anon_get(url)
        yield response.json()
        url = _get_next_url(response.headers)


def anon_public_timeline_generator(base_url, local=False, limit=20):
    params = {"local": str_bool(local), "limit": limit}
    url = f"{base_url}/api/v1/timelines/public"
    return _anon_timeline_generator(url, params)


def anon_tag_timeline_generator(base_url, hashtag, local=False, limit=20):
    query = {"local": str_bool(local), "limit": limit}
    url = f"{base_url}/api/v1/timelines/tag/{quote(hashtag)}"
    return _anon_timeline_generator(url, query)


def get_media(app: App, user: User, id: str):
    return http.get(app, user, f"/api/v1/media/{id}").json()


def upload_media(
    app: App,
    user: User,
    media: BinaryIO,
    description: Optional[str] = None,
    thumbnail: Optional[BinaryIO] = None,
):
    data = drop_empty_values({"description": description})

    # NB: Documentation says that "file" should provide a mime-type which we
    # don't do currently, but it works.
    files = drop_empty_values({
        "file": media,
        "thumbnail": _add_mime_type(thumbnail)
    })

    return http.post(app, user, "/api/v2/media", data=data, files=files)


def _add_mime_type(file):
    if file is None:
        return None

    # TODO: mimetypes uses the file extension to guess the mime type which is
    # not always good enough (e.g. files without extension). python-magic could
    # be used instead but it requires adding it as a dependency.
    mime_type = mimetypes.guess_type(file.name)

    if not mime_type:
        raise ConsoleError(f"Unable guess mime type of '{file.name}'. "
                           "Ensure the file has the desired extension.")

    filename = path.basename(file.name)
    return (filename, file, mime_type)


def search(
    app,
    user,
    query,
    resolve=False,
    type=None,
    offset=None,
    limit=None,
    min_id=None,
    max_id=None,
):
    """
    Perform a search.
    https://docs.joinmastodon.org/methods/search/#v2
    """
    params = drop_empty_values({
        "q": query,
        "resolve": str_bool(resolve),
        "type": type,
        "offset": offset,
        "limit": limit,
        "min_id": min_id,
        "max_id": max_id,
    })

    return http.get(app, user, "/api/v2/search", params)


def follow(app, user, account):
    return _account_action(app, user, account, 'follow')


def unfollow(app, user, account):
    return _account_action(app, user, account, 'unfollow')


def follow_tag(app, user, tag_name) -> Response:
    return _tag_action(app, user, tag_name, 'follow')


def unfollow_tag(app, user, tag_name) -> Response:
    return _tag_action(app, user, tag_name, 'unfollow')


def _get_response_list(app, user, path):
    items = []
    while path:
        response = http.get(app, user, path)
        items += response.json()
        path = _get_next_path(response.headers)
    return items


def following(app, user, account):
    path = f"/api/v1/accounts/{account}/following"
    return _get_response_list(app, user, path)


def followers(app, user, account):
    path = f"/api/v1/accounts/{account}/followers"
    return _get_response_list(app, user, path)


def followed_tags(app, user):
    path = '/api/v1/followed_tags'
    return _get_response_list(app, user, path)


def featured_tags(app, user):
    return http.get(app, user, "/api/v1/featured_tags")


def feature_tag(app, user, tag: str) -> Response:
    return http.post(app, user, "/api/v1/featured_tags", data={"name": tag})


def unfeature_tag(app, user, tag_id: str) -> Response:
    return http.delete(app, user, f"/api/v1/featured_tags/{tag_id}")


def find_tag(app, user, tag) -> Optional[dict]:
    """Find a hashtag by tag name or ID"""
    tag = tag.lstrip("#")
    results = search(app, user, tag, type="hashtags").json()

    return next(
        (
            t for t in results["hashtags"]
            if t["name"].lower() == tag.lstrip("#").lower() or t["id"] == tag
        ),
        None
    )


def find_featured_tag(app, user, tag) -> Optional[dict]:
    """Find a featured tag by tag name or ID"""
    return next(
        (
            t for t in featured_tags(app, user).json()
            if t["name"].lower() == tag.lstrip("#").lower() or t["id"] == tag
        ),
        None
    )


def whois(app, user, account):
    return http.get(app, user, f'/api/v1/accounts/{account}').json()


def vote(app, user, poll_id, choices: List[int]):
    url = f"/api/v1/polls/{poll_id}/votes"
    json = {'choices': choices}
    return http.post(app, user, url, json=json).json()


def get_relationship(app, user, account):
    params = {"id[]": account}
    return http.get(app, user, '/api/v1/accounts/relationships', params).json()[0]


def mute(app, user, account):
    return _account_action(app, user, account, 'mute')


def unmute(app, user, account):
    return _account_action(app, user, account, 'unmute')


def muted(app, user):
    return _get_response_list(app, user, "/api/v1/mutes")


def block(app, user, account):
    return _account_action(app, user, account, 'block')


def unblock(app, user, account):
    return _account_action(app, user, account, 'unblock')


def blocked(app, user):
    return _get_response_list(app, user, "/api/v1/blocks")


def verify_credentials(app, user) -> Response:
    return http.get(app, user, '/api/v1/accounts/verify_credentials')


def get_notifications(app, user, types=[], exclude_types=[], limit=20) -> Response:
    params = {"types[]": types, "exclude_types[]": exclude_types, "limit": limit}
    return http.get(app, user, '/api/v1/notifications', params)


def clear_notifications(app, user):
    http.post(app, user, '/api/v1/notifications/clear')


def get_instance(base_url: str) -> Response:
    url = f"{base_url}/api/v1/instance"
    return http.anon_get(url)


def get_preferences(app, user) -> Response:
    return http.get(app, user, '/api/v1/preferences')


def get_lists(app, user):
    return http.get(app, user, "/api/v1/lists").json()


def get_list_accounts(app, user, list_id):
    path = f"/api/v1/lists/{list_id}/accounts"
    return _get_response_list(app, user, path)


def create_list(app, user, title, replies_policy="none"):
    url = "/api/v1/lists"
    json = {'title': title}
    if replies_policy:
        json['replies_policy'] = replies_policy
    return http.post(app, user, url, json=json)


def delete_list(app, user, id):
    return http.delete(app, user, f"/api/v1/lists/{id}")


def add_accounts_to_list(app, user, list_id, account_ids):
    url = f"/api/v1/lists/{list_id}/accounts"
    json = {'account_ids': account_ids}
    return http.post(app, user, url, json=json)


def remove_accounts_from_list(app, user, list_id, account_ids):
    url = f"/api/v1/lists/{list_id}/accounts"
    json = {'account_ids': account_ids}
    return http.delete(app, user, url, json=json)
