# -*- coding: utf-8 -*-

from toot import App, User, api, config, auth
from tests.utils import retval


def test_register_app(monkeypatch):
    app_data = {'id': 100, 'client_id': 'cid', 'client_secret': 'cs'}

    def assert_app(app):
        assert isinstance(app, App)
        assert app.instance == "foo.bar"
        assert app.base_url == "https://foo.bar"
        assert app.client_id == "cid"
        assert app.client_secret == "cs"

    monkeypatch.setattr(api, 'create_app', retval(app_data))
    monkeypatch.setattr(config, 'save_app', assert_app)

    app = auth.register_app("foo.bar")
    assert_app(app)


def test_create_app_from_config(monkeypatch):
    """When there is saved config, it's returned"""
    monkeypatch.setattr(config, 'load_app', retval("loaded app"))
    app = auth.create_app_interactive("bezdomni.net")
    assert app == 'loaded app'


def test_create_app_registered(monkeypatch):
    """When there is no saved config, a new app is registered"""
    monkeypatch.setattr(config, 'load_app', retval(None))
    monkeypatch.setattr(auth, 'register_app', retval("registered app"))

    app = auth.create_app_interactive("bezdomni.net")
    assert app == 'registered app'


def test_create_user(monkeypatch):
    app = App(4, 5, 6, 7)

    def assert_user(user):
        assert isinstance(user, User)
        assert user.instance == app.instance
        assert user.username == 2
        assert user.access_token == 3

    monkeypatch.setattr(config, 'save_user', assert_user)

    user = auth.create_user(app, 2, 3)

    assert_user(user)

#
# TODO: figure out how to mock input so the rest can be tested
#
