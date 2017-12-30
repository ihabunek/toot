# -*- coding: utf-8 -*-
import pytest

from requests import Request

from toot import App, CLIENT_NAME, CLIENT_WEBSITE
from toot.api import create_app, login, SCOPES, AuthenticationError
from tests.utils import MockResponse, Expectations


def test_create_app(monkeypatch):
    request = Request('POST', 'https://bigfish.software/api/v1/apps',
                      data={'website': CLIENT_WEBSITE,
                            'client_name': CLIENT_NAME,
                            'scopes': SCOPES,
                            'redirect_uris': 'urn:ietf:wg:oauth:2.0:oob'})

    response = MockResponse({'client_id': 'foo',
                             'client_secret': 'bar'})

    e = Expectations()
    e.add(request, response)
    e.patch(monkeypatch)

    create_app('bigfish.software')


def test_login(monkeypatch):
    app = App('bigfish.software', 'https://bigfish.software', 'foo', 'bar')

    data = {
        'grant_type': 'password',
        'client_id': app.client_id,
        'client_secret': app.client_secret,
        'username': 'user',
        'password': 'pass',
        'scope': SCOPES,
    }

    request = Request('POST', 'https://bigfish.software/oauth/token', data=data)

    response = MockResponse({
        'token_type': 'bearer',
        'scope': 'read write follow',
        'access_token': 'xxx',
        'created_at': 1492523699
    })

    e = Expectations()
    e.add(request, response)
    e.patch(monkeypatch)

    login(app, 'user', 'pass')


def test_login_failed(monkeypatch):
    app = App('bigfish.software', 'https://bigfish.software', 'foo', 'bar')

    data = {
        'grant_type': 'password',
        'client_id': app.client_id,
        'client_secret': app.client_secret,
        'username': 'user',
        'password': 'pass',
        'scope': SCOPES,
    }

    request = Request('POST', 'https://bigfish.software/oauth/token', data=data)
    response = MockResponse(is_redirect=True)

    e = Expectations()
    e.add(request, response)
    e.patch(monkeypatch)

    with pytest.raises(AuthenticationError):
        login(app, 'user', 'pass')
