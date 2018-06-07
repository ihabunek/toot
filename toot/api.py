# -*- coding: utf-8 -*-

import re

from urllib.parse import urlparse, urlencode

from toot import http, CLIENT_NAME, CLIENT_WEBSITE
from toot.exceptions import AuthenticationError

SCOPES = 'read write follow'


def _account_action(app, user, account, action):
    url = '/api/v1/accounts/{}/{}'.format(account, action)

    return http.post(app, user, url).json()


def create_app(domain):
    url = 'https://{}/api/v1/apps'.format(domain)

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
        "scope": "read write follow",
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


def post_status(app, user, status, visibility='public', media_ids=None):
    return http.post(app, user, '/api/v1/statuses', {
        'status': status,
        'media_ids[]': media_ids,
        'visibility': visibility,
    }).json()


def timeline_home(app, user, args):
    if args.tag:
        timeline = "tag/%s" % args.tag
    else:
        timeline = "home"
    return http.get(app, user, '/api/v1/timelines/%s' % timeline).json()


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


def get_notifications(app, user):
    return http.get(app, user, '/api/v1/notifications').json()


def get_instance(domain):
    url = "http://{}/api/v1/instance".format(domain)
    return http.anon_get(url).json()
