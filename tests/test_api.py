import pytest

from unittest import mock

from toot import App, CLIENT_NAME, CLIENT_WEBSITE
from toot.api import create_app, login, SCOPES, AuthenticationError
from tests.utils import MockResponse


@mock.patch('toot.http.anon_post')
def test_create_app(mock_post):
    mock_post.return_value = MockResponse({
        'client_id': 'foo',
        'client_secret': 'bar',
    })

    create_app('https://bigfish.software')

    mock_post.assert_called_once_with('https://bigfish.software/api/v1/apps', json={
        'website': CLIENT_WEBSITE,
        'client_name': CLIENT_NAME,
        'scopes': SCOPES,
        'redirect_uris': 'urn:ietf:wg:oauth:2.0:oob',
    })


@mock.patch('toot.http.anon_post')
def test_login(mock_post):
    app = App('bigfish.software', 'https://bigfish.software', 'foo', 'bar')

    data = {
        'grant_type': 'password',
        'client_id': app.client_id,
        'client_secret': app.client_secret,
        'username': 'user',
        'password': 'pass',
        'scope': SCOPES,
    }

    mock_post.return_value = MockResponse({
        'token_type': 'bearer',
        'scope': 'read write follow',
        'access_token': 'xxx',
        'created_at': 1492523699
    })

    login(app, 'user', 'pass')

    mock_post.assert_called_once_with(
        'https://bigfish.software/oauth/token', data=data, allow_redirects=False)


@mock.patch('toot.http.anon_post')
def test_login_failed(mock_post):
    app = App('bigfish.software', 'https://bigfish.software', 'foo', 'bar')

    data = {
        'grant_type': 'password',
        'client_id': app.client_id,
        'client_secret': app.client_secret,
        'username': 'user',
        'password': 'pass',
        'scope': SCOPES,
    }

    mock_post.return_value = MockResponse(is_redirect=True)

    with pytest.raises(AuthenticationError):
        login(app, 'user', 'pass')

    mock_post.assert_called_once_with(
        'https://bigfish.software/oauth/token', data=data, allow_redirects=False)
