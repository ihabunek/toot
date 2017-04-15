import pytest
import requests
import sys

from toot import User, App
from toot.console import cmd_post_status, ConsoleError

from tests.utils import MockResponse

app = App('https://habunek.com', 'foo', 'bar')
user = User('ivan@habunek.com', 'xxx')


def test_post_status_defaults(monkeypatch):
    def mock_prepare(request):
        assert request.method == 'POST'
        assert request.url == 'https://habunek.com/api/v1/statuses'
        assert request.data == {
            'status': '"Hello world"',
            'visibility': 'public',
            'media_ids[]': None,
        }

    def mock_send(*args):
        return MockResponse({
            'url': 'http://ivan.habunek.com/'
        })

    monkeypatch.setattr(requests.Request, 'prepare', mock_prepare)
    monkeypatch.setattr(requests.Session, 'send', mock_send)

    sys.argv = ['toot', 'post', '"Hello world"']
    cmd_post_status(app, user)


def test_post_status_with_options(monkeypatch):
    def mock_prepare(request):
        assert request.method == 'POST'
        assert request.url == 'https://habunek.com/api/v1/statuses'
        assert request.data == {
            'status': '"Hello world"',
            'visibility': 'unlisted',
            'media_ids[]': None,
        }

    def mock_send(*args):
        return MockResponse({
            'url': 'http://ivan.habunek.com/'
        })

    monkeypatch.setattr(requests.Request, 'prepare', mock_prepare)
    monkeypatch.setattr(requests.Session, 'send', mock_send)

    sys.argv = ['toot', 'post', '"Hello world"',
                '--visibility', 'unlisted']

    cmd_post_status(app, user)


def test_post_status_invalid_visibility(monkeypatch):
    sys.argv = ['toot', 'post', '"Hello world"',
                '--visibility', 'foo']

    with pytest.raises(ConsoleError) as ex:
        cmd_post_status(app, user)
    assert str(ex.value) == "Invalid visibility value given: 'foo'"


def test_post_status_invalid_media(monkeypatch):
    sys.argv = ['toot', 'post', '"Hello world"',
                '--media', 'does_not_exist.jpg']

    with pytest.raises(ConsoleError) as ex:
        cmd_post_status(app, user)
    assert str(ex.value) == "File does not exist: does_not_exist.jpg"
