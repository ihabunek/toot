# -*- coding: utf-8 -*-
import pytest
import requests

from toot import App, CLIENT_NAME, CLIENT_WEBSITE
from toot.api import create_app, login, SCOPES, AuthenticationError
from tests.utils import MockResponse


def test_create_app(monkeypatch):
    response = {
        'client_id': 'foo',
        'client_secret': 'bar',
    }

    def mock_post(url, data):
        assert url == 'https://bigfish.software/api/v1/apps'
        assert data == {
            'website': CLIENT_WEBSITE,
            'client_name': CLIENT_NAME,
            'scopes': SCOPES,
            'redirect_uris': 'urn:ietf:wg:oauth:2.0:oob'
        }
        return MockResponse(response)

    monkeypatch.setattr(requests, 'post', mock_post)

    assert create_app('bigfish.software') == response


def test_login(monkeypatch):
    app = App('bigfish.software', 'https://bigfish.software', 'foo', 'bar')

    response = {
        'token_type': 'bearer',
        'scope': 'read write follow',
        'access_token': 'xxx',
        'created_at': 1492523699
    }

    def mock_post(url, data, allow_redirects):
        assert not allow_redirects
        assert url == 'https://bigfish.software/oauth/token'
        assert data == {
            'grant_type': 'password',
            'client_id': app.client_id,
            'client_secret': app.client_secret,
            'username': 'user',
            'password': 'pass',
            'scope': SCOPES,
        }

        return MockResponse(response)

    monkeypatch.setattr(requests, 'post', mock_post)

    assert login(app, 'user', 'pass') == response


def test_login_failed(monkeypatch):
    app = App('bigfish.software', 'https://bigfish.software', 'foo', 'bar')

    def mock_post(url, data, allow_redirects):
        assert not allow_redirects
        assert url == 'https://bigfish.software/oauth/token'
        assert data == {
            'grant_type': 'password',
            'client_id': app.client_id,
            'client_secret': app.client_secret,
            'username': 'user',
            'password': 'pass',
            'scope': SCOPES,
        }

        return MockResponse(is_redirect=True)

    monkeypatch.setattr(requests, 'post', mock_post)

    with pytest.raises(AuthenticationError):
        login(app, 'user', 'pass')
