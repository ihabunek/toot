import logging
import requests

from collections import namedtuple
from requests import Request, Session

App = namedtuple('App', ['base_url', 'client_id', 'client_secret'])
User = namedtuple('User', ['username', 'access_token'])

DEFAULT_INSTANCE = 'mastodon.social'

logger = logging.getLogger('toot')


def _log_request(request, prepared_request):
    logger.debug(">>> \033[32m{} {}\033[0m".format(request.method, request.url))
    logger.debug(">>> DATA:    \033[33m{}\033[0m".format(request.data))
    logger.debug(">>> FILES:   \033[33m{}\033[0m".format(request.files))
    logger.debug(">>> HEADERS: \033[33m{}\033[0m".format(request.headers))


def _log_response(response):
    logger.debug("<<< \033[32m{}\033[0m".format(response))
    logger.debug("<<< \033[33m{}\033[0m".format(response.json()))


def _get(app, user, url, params=None):
    url = app.base_url + url
    headers = {"Authorization": "Bearer " + user.access_token}

    response = requests.get(url, params, headers=headers)
    response.raise_for_status()

    return response.json()


def _post(app, user, url, data=None, files=None):
    url = app.base_url + url
    headers = {"Authorization": "Bearer " + user.access_token}

    session = Session()
    request = Request('POST', url, headers, files, data)
    prepared_request = request.prepare()

    _log_request(request, prepared_request)

    response = session.send(prepared_request)

    _log_response(response)

    response.raise_for_status()

    return response.json()


def create_app(base_url):
    url = base_url + '/api/v1/apps'

    response = requests.post(url, {
        'client_name': 'toot',
        'redirect_uris': 'urn:ietf:wg:oauth:2.0:oob',
        'scopes': 'read write',
        'website': 'https://github.com/ihabunek/toot',
    })

    response.raise_for_status()

    data = response.json()
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')

    return App(base_url, client_id, client_secret)


def login(app, username, password):
    url = app.base_url + '/oauth/token'

    response = requests.post(url, {
        'grant_type': 'password',
        'client_id': app.client_id,
        'client_secret': app.client_secret,
        'username': username,
        'password': password,
        'scope': 'read write',
    })

    response.raise_for_status()

    data = response.json()
    access_token = data.get('access_token')

    return User(username, access_token)


def post_status(app, user, status, visibility='public', media_ids=None):
    return _post(app, user, '/api/v1/statuses', {
        'status': status,
        'media_ids[]': media_ids,
        'visibility': visibility,
    })


def timeline_home(app, user):
    return _get(app, user, '/api/v1/timelines/home')


def upload_media(app, user, file):
    return _post(app, user, '/api/v1/media', files={
        'file': file
    })
