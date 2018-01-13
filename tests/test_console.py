# -*- coding: utf-8 -*-
import pytest
import requests
import re

from requests import Request

from toot import config, console, User, App
from toot.exceptions import ConsoleError

from tests.utils import MockResponse, Expectations

app = App('habunek.com', 'https://habunek.com', 'foo', 'bar')
user = User('habunek.com', 'ivan@habunek.com', 'xxx')


def uncolorize(text):
    """Remove ANSI color sequences from a string"""
    return re.sub(r'\x1b[^m]*m', '', text)


def test_print_usage(capsys):
    console.print_usage()
    out, err = capsys.readouterr()
    assert "toot - a Mastodon CLI client" in out


def test_post_defaults(monkeypatch, capsys):
    def mock_prepare(request):
        assert request.method == 'POST'
        assert request.url == 'https://habunek.com/api/v1/statuses'
        assert request.headers == {'Authorization': 'Bearer xxx'}
        assert request.data == {
            'status': 'Hello world',
            'visibility': 'public',
            'media_ids[]': None,
        }

    def mock_send(*args, **kwargs):
        return MockResponse({
            'url': 'http://ivan.habunek.com/'
        })

    monkeypatch.setattr(requests.Request, 'prepare', mock_prepare)
    monkeypatch.setattr(requests.Session, 'send', mock_send)

    console.run_command(app, user, 'post', ['Hello world'])

    out, err = capsys.readouterr()
    assert "Toot posted" in out


def test_post_with_options(monkeypatch, capsys):
    def mock_prepare(request):
        assert request.method == 'POST'
        assert request.url == 'https://habunek.com/api/v1/statuses'
        assert request.headers == {'Authorization': 'Bearer xxx'}
        assert request.data == {
            'status': '"Hello world"',
            'visibility': 'unlisted',
            'media_ids[]': None,
        }

    def mock_send(*args, **kwargs):
        return MockResponse({
            'url': 'http://ivan.habunek.com/'
        })

    monkeypatch.setattr(requests.Request, 'prepare', mock_prepare)
    monkeypatch.setattr(requests.Session, 'send', mock_send)

    args = ['"Hello world"', '--visibility', 'unlisted']

    console.run_command(app, user, 'post', args)

    out, err = capsys.readouterr()
    assert "Toot posted" in out


def test_post_invalid_visibility(monkeypatch, capsys):
    args = ['Hello world', '--visibility', 'foo']

    with pytest.raises(SystemExit):
        console.run_command(app, user, 'post', args)

    out, err = capsys.readouterr()
    assert "invalid visibility value: 'foo'" in err


def test_post_invalid_media(monkeypatch, capsys):
    args = ['Hello world', '--media', 'does_not_exist.jpg']

    with pytest.raises(SystemExit):
        console.run_command(app, user, 'post', args)

    out, err = capsys.readouterr()
    assert "can't open 'does_not_exist.jpg'" in err


def test_timeline(monkeypatch, capsys):
    def mock_prepare(request):
        assert request.url == 'https://habunek.com/api/v1/timelines/home'
        assert request.headers == {'Authorization': 'Bearer xxx'}
        assert request.params == {}

    def mock_send(*args, **kwargs):
        return MockResponse([{
            'account': {
                'display_name': 'Frank Zappa',
                'username': 'fz'
            },
            'created_at': '2017-04-12T15:53:18.174Z',
            'content': "<p>The computer can't tell you the emotional story. It can give you the exact mathematical design, but what's missing is the eyebrows.</p>",
            'reblog': None,
        }])

    monkeypatch.setattr(requests.Request, 'prepare', mock_prepare)
    monkeypatch.setattr(requests.Session, 'send', mock_send)

    console.run_command(app, user, 'timeline', [])

    out, err = capsys.readouterr()
    assert "The computer can't tell you the emotional story." in out
    assert "Frank Zappa @fz" in out


def test_upload(monkeypatch, capsys):
    def mock_prepare(request):
        assert request.method == 'POST'
        assert request.url == 'https://habunek.com/api/v1/media'
        assert request.headers == {'Authorization': 'Bearer xxx'}
        assert request.files.get('file') is not None

    def mock_send(*args, **kwargs):
        return MockResponse({
            'id': 123,
            'url': 'https://bigfish.software/123/456',
            'preview_url': 'https://bigfish.software/789/012',
            'text_url': 'https://bigfish.software/345/678',
            'type': 'image',
        })

    monkeypatch.setattr(requests.Request, 'prepare', mock_prepare)
    monkeypatch.setattr(requests.Session, 'send', mock_send)

    console.run_command(app, user, 'upload', [__file__])

    out, err = capsys.readouterr()
    assert "Uploading media" in out
    assert __file__ in out


def test_search(monkeypatch, capsys):
    def mock_prepare(request):
        assert request.url == 'https://habunek.com/api/v1/search'
        assert request.headers == {'Authorization': 'Bearer xxx'}
        assert request.params == {
            'q': 'freddy',
            'resolve': False,
        }

    def mock_send(*args, **kwargs):
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

    monkeypatch.setattr(requests.Request, 'prepare', mock_prepare)
    monkeypatch.setattr(requests.Session, 'send', mock_send)

    console.run_command(app, user, 'search', ['freddy'])

    out, err = capsys.readouterr()
    assert "Hashtags:\n\033[32m#foo\033[0m, \033[32m#bar\033[0m, \033[32m#baz\033[0m" in out
    assert "Accounts:" in out
    assert "\033[32m@thequeen\033[0m Freddy Mercury" in out
    assert "\033[32m@thequeen@other.instance\033[0m Mercury Freddy" in out


def test_follow(monkeypatch, capsys):
    req1 = Request('GET', 'https://habunek.com/api/v1/accounts/search',
                   params={'q': 'blixa'},
                   headers={'Authorization': 'Bearer xxx'})
    res1 = MockResponse([
        {'id': 123, 'acct': 'blixa@other.acc'},
        {'id': 321, 'acct': 'blixa'},
    ])

    req2 = Request('POST', 'https://habunek.com/api/v1/accounts/321/follow',
                   headers={'Authorization': 'Bearer xxx'})
    res2 = MockResponse()

    expectations = Expectations([req1, req2], [res1, res2])
    expectations.patch(monkeypatch)

    console.run_command(app, user, 'follow', ['blixa'])

    out, err = capsys.readouterr()
    assert "You are now following blixa" in out


def test_follow_not_found(monkeypatch, capsys):
    req = Request('GET', 'https://habunek.com/api/v1/accounts/search',
                  params={'q': 'blixa'}, headers={'Authorization': 'Bearer xxx'})
    res = MockResponse()

    expectations = Expectations([req], [res])
    expectations.patch(monkeypatch)

    with pytest.raises(ConsoleError) as ex:
        console.run_command(app, user, 'follow', ['blixa'])
    assert "Account not found" == str(ex.value)


def test_unfollow(monkeypatch, capsys):
    req1 = Request('GET', 'https://habunek.com/api/v1/accounts/search',
                   params={'q': 'blixa'},
                   headers={'Authorization': 'Bearer xxx'})
    res1 = MockResponse([
        {'id': 123, 'acct': 'blixa@other.acc'},
        {'id': 321, 'acct': 'blixa'},
    ])

    req2 = Request('POST', 'https://habunek.com/api/v1/accounts/321/unfollow',
                   headers={'Authorization': 'Bearer xxx'})
    res2 = MockResponse()

    expectations = Expectations([req1, req2], [res1, res2])
    expectations.patch(monkeypatch)

    console.run_command(app, user, 'unfollow', ['blixa'])

    out, err = capsys.readouterr()
    assert "You are no longer following blixa" in out


def test_unfollow_not_found(monkeypatch, capsys):
    req = Request('GET', 'https://habunek.com/api/v1/accounts/search',
                  params={'q': 'blixa'}, headers={'Authorization': 'Bearer xxx'})
    res = MockResponse([])

    expectations = Expectations([req], [res])
    expectations.patch(monkeypatch)

    with pytest.raises(ConsoleError) as ex:
        console.run_command(app, user, 'unfollow', ['blixa'])
    assert "Account not found" == str(ex.value)


def test_whoami(monkeypatch, capsys):
    req = Request('GET', 'https://habunek.com/api/v1/accounts/verify_credentials',
                  headers={'Authorization': 'Bearer xxx'})

    res = MockResponse({
        'acct': 'ihabunek',
        'avatar': 'https://files.mastodon.social/accounts/avatars/000/046/103/original/6a1304e135cac514.jpg?1491312434',
        'avatar_static': 'https://files.mastodon.social/accounts/avatars/000/046/103/original/6a1304e135cac514.jpg?1491312434',
        'created_at': '2017-04-04T13:23:09.777Z',
        'display_name': 'Ivan Habunek',
        'followers_count': 5,
        'following_count': 9,
        'header': '/headers/original/missing.png',
        'header_static': '/headers/original/missing.png',
        'id': 46103,
        'locked': False,
        'note': 'A developer.',
        'statuses_count': 19,
        'url': 'https://mastodon.social/@ihabunek',
        'username': 'ihabunek'
    })

    expectations = Expectations([req], [res])
    expectations.patch(monkeypatch)

    console.run_command(app, user, 'whoami', [])

    out, err = capsys.readouterr()
    out = uncolorize(out)

    assert "@ihabunek Ivan Habunek" in out
    assert "A developer." in out
    assert "https://mastodon.social/@ihabunek" in out
    assert "ID: 46103" in out
    assert "Since: 2017-04-04 @ 13:23:09" in out
    assert "Followers: 5" in out
    assert "Following: 9" in out
    assert "Statuses: 19" in out


def u(user_id, access_token="abc"):
    username, instance = user_id.split("@")
    return {
        "instance": instance,
        "username": username,
        "access_token": access_token,
    }


def test_logout(monkeypatch, capsys):
    def mock_load():
        return {
            "users": {
                "king@gizzard.social": u("king@gizzard.social"),
                "lizard@wizard.social": u("lizard@wizard.social"),
            },
            "active_user": "king@gizzard.social",
        }

    def mock_save(config):
        assert config["users"] == {
            "lizard@wizard.social": u("lizard@wizard.social")
        }
        assert config["active_user"] is None

    monkeypatch.setattr(config, "load_config", mock_load)
    monkeypatch.setattr(config, "save_config", mock_save)

    console.run_command(None, None, "logout", ["king@gizzard.social"])

    out, err = capsys.readouterr()
    assert "✓ User king@gizzard.social logged out" in out


def test_activate(monkeypatch, capsys):
    def mock_load():
        return {
            "users": {
                "king@gizzard.social": u("king@gizzard.social"),
                "lizard@wizard.social": u("lizard@wizard.social"),
            },
            "active_user": "king@gizzard.social",
        }

    def mock_save(config):
        assert config["users"] == {
            "king@gizzard.social": u("king@gizzard.social"),
            "lizard@wizard.social": u("lizard@wizard.social"),
        }
        assert config["active_user"] == "lizard@wizard.social"

    monkeypatch.setattr(config, "load_config", mock_load)
    monkeypatch.setattr(config, "save_config", mock_save)

    console.run_command(None, None, "activate", ["lizard@wizard.social"])

    out, err = capsys.readouterr()
    assert "✓ User lizard@wizard.social active" in out
