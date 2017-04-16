# -*- coding: utf-8 -*-
import pytest
import requests

from toot import User, App
from toot.console import print_usage, cmd_post_status, cmd_timeline, cmd_upload, cmd_search

from tests.utils import MockResponse

app = App('https://habunek.com', 'foo', 'bar')
user = User('ivan@habunek.com', 'xxx')


def test_print_usagecap(capsys):
    print_usage()
    out, err = capsys.readouterr()
    assert "toot - interact with Mastodon from the command line" in out


def test_post_status_defaults(monkeypatch, capsys):
    def mock_prepare(request):
        assert request.method == 'POST'
        assert request.url == 'https://habunek.com/api/v1/statuses'
        assert request.headers == {'Authorization': 'Bearer xxx'}
        assert request.data == {
            'status': 'Hello world',
            'visibility': 'public',
            'media_ids[]': None,
        }

    def mock_send(*args):
        return MockResponse({
            'url': 'http://ivan.habunek.com/'
        })

    monkeypatch.setattr(requests.Request, 'prepare', mock_prepare)
    monkeypatch.setattr(requests.Session, 'send', mock_send)

    cmd_post_status(app, user, ['Hello world'])

    out, err = capsys.readouterr()
    assert "Toot posted" in out


def test_post_status_with_options(monkeypatch, capsys):
    def mock_prepare(request):
        assert request.method == 'POST'
        assert request.url == 'https://habunek.com/api/v1/statuses'
        assert request.headers == {'Authorization': 'Bearer xxx'}
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

    args = ['"Hello world"', '--visibility', 'unlisted']

    cmd_post_status(app, user, args)

    out, err = capsys.readouterr()
    assert "Toot posted" in out


def test_post_status_invalid_visibility(monkeypatch, capsys):
    args = ['Hello world', '--visibility', 'foo']

    with pytest.raises(SystemExit):
        cmd_post_status(app, user, args)

    out, err = capsys.readouterr()
    assert "invalid visibility value: 'foo'" in err


def test_post_status_invalid_media(monkeypatch, capsys):
    args = ['Hello world', '--media', 'does_not_exist.jpg']

    with pytest.raises(SystemExit):
        cmd_post_status(app, user, args)

    out, err = capsys.readouterr()
    assert "can't open 'does_not_exist.jpg'" in err


def test_timeline(monkeypatch, capsys):
    def mock_get(url, params, headers=None):
        assert url == 'https://habunek.com/api/v1/timelines/home'
        assert headers == {'Authorization': 'Bearer xxx'}
        assert params is None

        return MockResponse([{
            'account': {
                'display_name': 'Frank Zappa',
                'username': 'fz'
            },
            'created_at': '2017-04-12T15:53:18.174Z',
            'content': "<p>The computer can't tell you the emotional story. It can give you the exact mathematical design, but what's missing is the eyebrows.</p>",
            'reblog': None,
        }])

    monkeypatch.setattr(requests, 'get', mock_get)

    cmd_timeline(app, user, [])

    out, err = capsys.readouterr()
    assert "The computer can't tell you the emotional story." in out
    assert "Frank Zappa @fz" in out


def test_upload(monkeypatch, capsys):
    def mock_prepare(request):
        assert request.method == 'POST'
        assert request.url == 'https://habunek.com/api/v1/media'
        assert request.headers == {'Authorization': 'Bearer xxx'}
        assert request.files.get('file') is not None

    def mock_send(*args):
        return MockResponse({
            'id': 123,
            'url': 'https://bigfish.software/123/456',
            'preview_url': 'https://bigfish.software/789/012',
            'text_url': 'https://bigfish.software/345/678',
            'type': 'image',
        })

    monkeypatch.setattr(requests.Request, 'prepare', mock_prepare)
    monkeypatch.setattr(requests.Session, 'send', mock_send)

    cmd_upload(app, user, [__file__])

    out, err = capsys.readouterr()
    assert "Uploading media" in out
    assert __file__ in out


def test_search(monkeypatch, capsys):
    def mock_get(url, params, headers=None):
        assert url == 'https://habunek.com/api/v1/search'
        assert headers == {'Authorization': 'Bearer xxx'}
        assert params == {
            'q': 'freddy',
            'resolve': False,
        }

        return MockResponse({
            'hashtags': ['foo', 'bar', 'baz'],
            'accounts': [{
                'acct': 'thequeen',
                'display_name': 'Freddy Mercury'
            }, {
                'acct': 'thequeen@other.instance',
                'display_name': 'Mercury Freddy'
            }],
            'statuses': [],
        })

    monkeypatch.setattr(requests, 'get', mock_get)

    cmd_search(app, user, ['freddy'])

    out, err = capsys.readouterr()
    assert "Hashtags:\n\033[32m#foo\033[0m, \033[32m#bar\033[0m, \033[32m#baz\033[0m" in out
    assert "Accounts:" in out
    assert "\033[32m@thequeen\033[0m Freddy Mercury" in out
    assert "\033[32m@thequeen@other.instance\033[0m Mercury Freddy" in out
