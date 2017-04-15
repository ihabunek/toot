# -*- coding: utf-8 -*-
import requests

from toot import App, User, create_app, login, CLIENT_NAME, CLIENT_WEB, SCOPES


class MockResponse:
    def __init__(self, response_data={}):
        self.response_data = response_data

    def raise_for_status(self):
        pass

    def json(self):
        return self.response_data


def test_create_app(monkeypatch):
    def mock_post(url, data):
        assert url == 'https://bigfish.software/api/v1/apps'
        assert data == {
            'website': CLIENT_WEB,
            'client_name': CLIENT_NAME,
            'scopes': SCOPES,
            'redirect_uris': 'urn:ietf:wg:oauth:2.0:oob'
        }
        return MockResponse({
            'client_id': 'foo',
            'client_secret': 'bar',
        })

    monkeypatch.setattr(requests, 'post', mock_post)

    app = create_app('https://bigfish.software')

    assert isinstance(app, App)
    assert app.client_id == 'foo'
    assert app.client_secret == 'bar'


def test_login(monkeypatch):
    app = App('https://bigfish.software', 'foo', 'bar')

    def mock_post(url, data):
        assert url == 'https://bigfish.software/oauth/token'
        assert data == {
            'grant_type': 'password',
            'client_id': app.client_id,
            'client_secret': app.client_secret,
            'username': 'user',
            'password': 'pass',
            'scope': SCOPES,
        }
        return MockResponse({
            'access_token': 'xxx',
        })

    monkeypatch.setattr(requests, 'post', mock_post)

    user = login(app, 'user', 'pass')

    assert isinstance(user, User)
    assert user.username == 'user'
    assert user.access_token == 'xxx'
