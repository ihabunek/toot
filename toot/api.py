# -*- coding: utf-8 -*-

import re
import uuid

from urllib.parse import urlparse, urlencode, quote

from toot import http, CLIENT_NAME, CLIENT_WEBSITE
from toot.exceptions import AuthenticationError

SCOPES = 'read write follow'


def _account_action(app, user, account, action):
    url = '/api/v1/accounts/{}/{}'.format(account, action)

    return http.post(app, user, url).json()


def _status_action(app, user, status_id, action):
    url = '/api/v1/statuses/{}/{}'.format(status_id, action)

    return http.post(app, user, url).json()


def create_app(domain, scheme='https'):
    url = '{}://{}/api/v1/apps'.format(scheme, domain)

    data = {
        'client_name': CLIENT_NAME,
        'redirect_uris': 'urn:ietf:wg:oauth:2.0:oob',
        'scopes': SCOPES,
        'website': CLIENT_WEBSITE,
    }

    return http.anon_post(url, data).json()


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

    response = http.anon_post(url, data, allow_redirects=False)

    # If auth fails, it redirects to the login page
    if response.is_redirect:
        raise AuthenticationError()

    return http.process_response(response).json()


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

    response = http.anon_post(url, data, allow_redirects=False)

    return http.process_response(response).json()


def post_status(
    app,
    user,
    status,
    visibility='public',
    media_ids=None,
    sensitive=False,
    spoiler_text=None,
    in_reply_to_id=None
):
    """
    Posts a new status.
    https://github.com/tootsuite/documentation/blob/master/Using-the-API/API.md#posting-a-new-status
    """

    # Idempotency key assures the same status is not posted multiple times
    # if the request is retried.
    headers = {"Idempotency-Key": uuid.uuid4().hex}

    return http.post(app, user, '/api/v1/statuses', {
        'status': status,
        'media_ids[]': media_ids,
        'visibility': visibility,
        'sensitive': "true" if sensitive else "false",
        'spoiler_text': spoiler_text,
        'in_reply_to_id': in_reply_to_id,
    }, headers=headers).json()


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


def context(app, user, status_id):
    url = '/api/v1/statuses/{}/context'.format(status_id)

    return http.get(app, user, url).json()


def reblogged_by(app, user, status_id):
    url = '/api/v1/statuses/{}/reblogged_by'.format(status_id)

    return http.get(app, user, url).json()


def timeline_home(app, user):
    return http.get(app, user, '/api/v1/timelines/home').json()


def timeline_public(app, user, local=False):
    params = {'local': 'true' if local else 'false'}
    return http.get(app, user, '/api/v1/timelines/public', params).json()


def timeline_tag(app, user, hashtag, local=False):
    url = '/api/v1/timelines/tag/{}'.format(quote(hashtag))
    params = {'local': 'true' if local else 'false'}
    return http.get(app, user, url, params).json()


def timeline_list(app, user, list_id):
    url = '/api/v1/timelines/list/{}'.format(list_id)
    return http.get(app, user, url).json()


def get_next_path(headers):
    """Given timeline response headers, returns the path to the next batch"""
    links = headers.get('Link', '')
    matches = re.match('<([^>]+)>; rel="next"', links)
    if matches:
        parsed = urlparse(matches.group(1))
        return "?".join([parsed.path, parsed.query])


def _timeline_generator(app, user, path, limit=20):
    while path:
        response = http.get(app, user, path)
        yield response.json()
        path = get_next_path(response.headers)


def _anon_timeline_generator(instance, path, limit=20):
    while path:
        url = "https://{}{}".format(instance, path)
        response = http.anon_get(url, path)
        yield response.json()
        path = get_next_path(response.headers)


def home_timeline_generator(app, user, limit=20):
    path = '/api/v1/timelines/home?limit={}'.format(limit)
    return _timeline_generator(app, user, path)


def public_timeline_generator(instance, limit=20):
    path = '/api/v1/timelines/public?limit={}'.format(limit)
    return _anon_timeline_generator(instance, path)


def upload_media(app, user, file):
    return http.post(app, user, '/api/v1/media', files={
        'file': file
    }).json()


def search(app, user, query, resolve):
    return http.get(app, user, '/api/v1/search', {
        'q': query,
        'resolve': resolve,
    }).json()


def search_accounts(app, user, query):
    return http.get(app, user, '/api/v1/accounts/search', {
        'q': query,
    }).json()


def follow(app, user, account):
    return _account_action(app, user, account, 'follow')


def unfollow(app, user, account):
    return _account_action(app, user, account, 'unfollow')


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


def get_notifications(app, user):
    return http.get(app, user, '/api/v1/notifications').json()


def get_instance(domain, scheme="https"):
    url = "{}://{}/api/v1/instance".format(scheme, domain)
    return http.anon_get(url).json()
