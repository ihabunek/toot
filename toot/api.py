# -*- coding: utf-8 -*-

import re
import uuid

from urllib.parse import urlparse, urlencode, quote

from toot import http, CLIENT_NAME, CLIENT_WEBSITE
from toot.exceptions import AuthenticationError
from toot.utils import str_bool

SCOPES = 'read write follow'


def _account_action(app, user, account, action):
    url = '/api/v1/accounts/{}/{}'.format(account, action)

    return http.post(app, user, url).json()


def _status_action(app, user, status_id, action):
    url = '/api/v1/statuses/{}/{}'.format(status_id, action)

    return http.post(app, user, url).json()


def create_app(domain, scheme='https'):
    url = '{}://{}/api/v1/apps'.format(scheme, domain)

    json = {
        'client_name': CLIENT_NAME,
        'redirect_uris': 'urn:ietf:wg:oauth:2.0:oob',
        'scopes': SCOPES,
        'website': CLIENT_WEBSITE,
    }

    return http.anon_post(url, json=json).json()


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


def fetch_app_token(app):
    json = {
        "client_id": app.client_id,
        "client_secret": app.client_secret,
        "grant_type": "client_credentials",
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "scope": "read write"
    }

    return http.anon_post(f"{app.base_url}/oauth/token", json=json).json()


def login(app, username, password):
    url = app.base_url + '/oauth/token'

    data = {
        'grant_type': 'password',
        'client_id': app.client_id,
        'client_secret': app.client_secret,
        'username': username,
        'password': password,
        'scope': SCOPES,
    }

    response = http.anon_post(url, data=data, allow_redirects=False)

    # If auth fails, it redirects to the login page
    if response.is_redirect:
        raise AuthenticationError()

    return response.json()


def get_browser_login_url(app):
    """Returns the URL for manual log in via browser"""
    return "{}/oauth/authorize/?{}".format(app.base_url, urlencode({
        "response_type": "code",
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "scope": SCOPES,
        "client_id": app.client_id,
    }))


def request_access_token(app, authorization_code):
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
    visibility='public',
    media_ids=None,
    sensitive=False,
    spoiler_text=None,
    in_reply_to_id=None,
    language=None,
    scheduled_at=None,
    content_type=None,
):
    """
    Publish a new status.
    https://docs.joinmastodon.org/methods/statuses/#create
    """

    # Idempotency key assures the same status is not posted multiple times
    # if the request is retried.
    headers = {"Idempotency-Key": uuid.uuid4().hex}

    json = {
        'status': status,
        'media_ids': media_ids,
        'visibility': visibility,
        'sensitive': sensitive,
        'in_reply_to_id': in_reply_to_id,
        'language': language,
        'scheduled_at': scheduled_at,
        'content_type': content_type,
        'spoiler_text': spoiler_text
    }

    # Strip keys for which value is None
    # Sending null values doesn't bother Mastodon, but it breaks Pleroma
    json = {k: v for k, v in json.items() if v is not None}

    return http.post(app, user, '/api/v1/statuses', json=json, headers=headers).json()


def fetch_status(app, user, id):
    """
    Fetch a single status
    https://docs.joinmastodon.org/methods/statuses/#get
    """
    return http.get(app, user, f"/api/v1/statuses/{id}").json()


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
    return http.delete(app, user, '/api/v1/statuses/{}'.format(status_id))


def favourite(app, user, status_id):
    return _status_action(app, user, status_id, 'favourite')


def unfavourite(app, user, status_id):
    return _status_action(app, user, status_id, 'unfavourite')


def reblog(app, user, status_id):
    return _status_action(app, user, status_id, 'reblog')


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


def context(app, user, status_id):
    url = '/api/v1/statuses/{}/context'.format(status_id)

    return http.get(app, user, url).json()


def reblogged_by(app, user, status_id):
    url = '/api/v1/statuses/{}/reblogged_by'.format(status_id)

    return http.get(app, user, url).json()


def _get_next_path(headers):
    """Given timeline response headers, returns the path to the next batch"""
    links = headers.get('Link', '')
    matches = re.match('<([^>]+)>; rel="next"', links)
    if matches:
        parsed = urlparse(matches.group(1))
        return "?".join([parsed.path, parsed.query])


def _timeline_generator(app, user, path, params=None):
    while path:
        response = http.get(app, user, path, params)
        yield response.json()
        path = _get_next_path(response.headers)


def home_timeline_generator(app, user, limit=20):
    path = '/api/v1/timelines/home?limit={}'.format(limit)
    return _timeline_generator(app, user, path)


def public_timeline_generator(app, user, local=False, limit=20):
    path = '/api/v1/timelines/public'
    params = {'local': str_bool(local), 'limit': limit}
    return _timeline_generator(app, user, path, params)


def tag_timeline_generator(app, user, hashtag, local=False, limit=20):
    path = '/api/v1/timelines/tag/{}'.format(quote(hashtag))
    params = {'local': str_bool(local), 'limit': limit}
    return _timeline_generator(app, user, path, params)


def timeline_list_generator(app, user, list_id, limit=20):
    path = '/api/v1/timelines/list/{}'.format(list_id)
    return _timeline_generator(app, user, path, {'limit': limit})


def _anon_timeline_generator(instance, path, params=None):
    while path:
        url = "https://{}{}".format(instance, path)
        response = http.anon_get(url, params)
        yield response.json()
        path = _get_next_path(response.headers)


def anon_public_timeline_generator(instance, local=False, limit=20):
    path = '/api/v1/timelines/public'
    params = {'local': str_bool(local), 'limit': limit}
    return _anon_timeline_generator(instance, path, params)


def anon_tag_timeline_generator(instance, hashtag, local=False, limit=20):
    path = '/api/v1/timelines/tag/{}'.format(quote(hashtag))
    params = {'local': str_bool(local), 'limit': limit}
    return _anon_timeline_generator(instance, path, params)


def upload_media(app, user, file, description=None):
    return http.post(app, user, '/api/v1/media',
        data={'description': description},
        files={'file': file}
    ).json()


def search(app, user, query, resolve=False, type=None):
    """
    Perform a search.
    https://docs.joinmastodon.org/methods/search/#v2
    """
    return http.get(app, user, "/api/v2/search", {
        "q": query,
        "resolve": resolve,
        "type": type
    }).json()


def follow(app, user, account):
    return _account_action(app, user, account, 'follow')


def unfollow(app, user, account):
    return _account_action(app, user, account, 'unfollow')


def _get_account_list(app, user, path):
    accounts = []
    while path:
        response = http.get(app, user, path)
        accounts += response.json()
        path = _get_next_path(response.headers)
    return accounts


def following(app, user, account):
    path = '/api/v1/accounts/{}/{}'.format(account, 'following')
    return _get_account_list(app, user, path)


def followers(app, user, account):
    path = '/api/v1/accounts/{}/{}'.format(account, 'followers')
    return _get_account_list(app, user, path)


def mute(app, user, account):
    return _account_action(app, user, account, 'mute')


def unmute(app, user, account):
    return _account_action(app, user, account, 'unmute')


def block(app, user, account):
    return _account_action(app, user, account, 'block')


def unblock(app, user, account):
    return _account_action(app, user, account, 'unblock')


def verify_credentials(app, user):
    return http.get(app, user, '/api/v1/accounts/verify_credentials').json()


def single_status(app, user, status_id):
    url = '/api/v1/statuses/{}'.format(status_id)

    return http.get(app, user, url).json()


def get_notifications(app, user, exclude_types=[], limit=20):
    params = {"exclude_types[]": exclude_types, "limit": limit}
    return http.get(app, user, '/api/v1/notifications', params).json()


def clear_notifications(app, user):
    http.post(app, user, '/api/v1/notifications/clear')


def get_instance(domain, scheme="https"):
    url = "{}://{}/api/v1/instance".format(scheme, domain)
    return http.anon_get(url).json()
