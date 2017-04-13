import requests

from collections import namedtuple

App = namedtuple('App', ['base_url', 'client_id', 'client_secret'])
User = namedtuple('User', ['username', 'access_token'])

APP_NAME = 'toot'
DEFAULT_INSTANCE = 'mastodon.social'


def _get(app, user, url, params=None):
    url = app.base_url + url
    headers = {"Authorization": "Bearer " + user.access_token}

    response = requests.get(url, params, headers=headers)
    response.raise_for_status()

    return response.json()


def _post(app, user, url, data=None):
    url = app.base_url + url
    headers = {"Authorization": "Bearer " + user.access_token}

    response = requests.post(url, data, headers=headers)
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


def post_status(app, user, status):
    return _post(app, user, '/api/v1/statuses', {
        'status': status
    })


def timeline_home(app, user):
    return _get(app, user, '/api/v1/timelines/home')
