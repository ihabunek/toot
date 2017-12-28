# -*- coding: utf-8 -*-

import logging
import re
import requests

from urllib.parse import urlparse, urlencode
from requests import Request, Session

from toot import CLIENT_NAME, CLIENT_WEBSITE

SCOPES = 'read write follow'

logger = logging.getLogger('toot')


class ApiError(Exception):
    pass


class NotFoundError(ApiError):
    pass


class AuthenticationError(ApiError):
    pass


def _log_request(request):
    logger.debug(">>> \033[32m{} {}\033[0m".format(request.method, request.url))
    logger.debug(">>> HEADERS: \033[33m{}\033[0m".format(request.headers))

    if request.data:
        logger.debug(">>> DATA:    \033[33m{}\033[0m".format(request.data))

    if request.files:
        logger.debug(">>> FILES:   \033[33m{}\033[0m".format(request.files))

    if request.params:
        logger.debug(">>> PARAMS:  \033[33m{}\033[0m".format(request.params))


def _log_response(response):
    if response.ok:
        logger.debug("<<< \033[32m{}\033[0m".format(response))
        logger.debug("<<< \033[33m{}\033[0m".format(response.json()))
    else:
        logger.debug("<<< \033[31m{}\033[0m".format(response))
        logger.debug("<<< \033[31m{}\033[0m".format(response.content))


def _process_response(response):
    _log_response(response)

    if not response.ok:
        error = "Unknown error"

        try:
            data = response.json()
            if "error_description" in data:
                error = data['error_description']
            elif "error" in data:
                error = data['error']
        except:
            pass

        if response.status_code == 404:
            raise NotFoundError(error)

        raise ApiError(error)

    return response


def _get(app, user, url, params=None):
    url = app.base_url + url
    headers = {"Authorization": "Bearer " + user.access_token}

    _log_request(Request('GET', url, headers, params=params))

    response = requests.get(url, params, headers=headers)

    return _process_response(response)


def _post(app, user, url, data=None, files=None):
    url = app.base_url + url
    headers = {"Authorization": "Bearer " + user.access_token}

    session = Session()
    request = Request('POST', url, headers, files, data)
    prepared_request = request.prepare()

    _log_request(request)

    response = session.send(prepared_request)

    return _process_response(response)


def _account_action(app, user, account, action):
    url = '/api/v1/accounts/{}/{}'.format(account, action)

    return _post(app, user, url).json()


def create_app(instance):
    base_url = 'https://' + instance
    url = base_url + '/api/v1/apps'

    response = requests.post(url, {
        'client_name': CLIENT_NAME,
        'redirect_uris': 'urn:ietf:wg:oauth:2.0:oob',
        'scopes': SCOPES,
        'website': CLIENT_WEBSITE,
    })

    return _process_response(response).json()


def login(app, username, password):
    url = app.base_url + '/oauth/token'

    response = requests.post(url, {
        'grant_type': 'password',
        'client_id': app.client_id,
        'client_secret': app.client_secret,
        'username': username,
        'password': password,
        'scope': SCOPES,
    }, allow_redirects=False)

    # If auth fails, it redirects to the login page
    if response.is_redirect:
        raise AuthenticationError()

    return _process_response(response).json()


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

    response = requests.post(url, {
        'grant_type': 'authorization_code',
        'client_id': app.client_id,
        'client_secret': app.client_secret,
        'code': authorization_code,
        'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
    }, allow_redirects=False)

    return _process_response(response).json()


def post_status(app, user, status, visibility='public', media_ids=None):
    return _post(app, user, '/api/v1/statuses', {
        'status': status,
        'media_ids[]': media_ids,
        'visibility': visibility,
    }).json()


def timeline_home(app, user):
    return _get(app, user, '/api/v1/timelines/home').json()


def _get_next_path(headers):
    links = headers.get('Link', '')
    matches = re.match('<([^>]+)>; rel="next"', links)
    if matches:
        url = matches.group(1)
        return urlparse(url).path


def timeline_generator(app, user):
    next_path = '/api/v1/timelines/home'

    while next_path:
        response = _get(app, user, next_path)
        yield response.json()
        next_path = _get_next_path(response.headers)


def upload_media(app, user, file):
    return _post(app, user, '/api/v1/media', files={
        'file': file
    }).json()


def search(app, user, query, resolve):
    return _get(app, user, '/api/v1/search', {
        'q': query,
        'resolve': resolve,
    }).json()


def search_accounts(app, user, query):
    return _get(app, user, '/api/v1/accounts/search', {
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
    return _get(app, user, '/api/v1/accounts/verify_credentials').json()


def get_notifications(app, user):
    return _get(app, user, '/api/v1/notifications').json()
