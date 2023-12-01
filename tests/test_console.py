import io
import pytest
import re

from collections import namedtuple
from unittest import mock

from toot import console, User, App, http
from toot.exceptions import ConsoleError

from tests.utils import MockResponse

app = App('habunek.com', 'https://habunek.com', 'foo', 'bar')
user = User('habunek.com', 'ivan@habunek.com', 'xxx')

MockUuid = namedtuple("MockUuid", ["hex"])


def uncolorize(text):
    """Remove ANSI color sequences from a string"""
    return re.sub(r'\x1b[^m]*m', '', text)


def test_print_usage(capsys):
    console.print_usage()
    out, err = capsys.readouterr()
    assert "toot - a Mastodon CLI client" in out


@mock.patch('uuid.uuid4')
@mock.patch('toot.http.post')
def test_post_defaults(mock_post, mock_uuid, capsys):
    mock_uuid.return_value = MockUuid("rock-on")
    mock_post.return_value = MockResponse({
        'url': 'https://habunek.com/@ihabunek/1234567890'
    })

    console.run_command(app, user, 'post', ['Hello world'])

    mock_post.assert_called_once_with(app, user, '/api/v1/statuses', json={
        'status': 'Hello world',
        'visibility': 'public',
        'media_ids': [],
        'sensitive': False,
    }, headers={"Idempotency-Key": "rock-on"})

    out, err = capsys.readouterr()
    assert 'Toot posted' in out
    assert 'https://habunek.com/@ihabunek/1234567890' in out
    assert not err


@mock.patch('uuid.uuid4')
@mock.patch('toot.http.post')
def test_post_with_options(mock_post, mock_uuid, capsys):
    mock_uuid.return_value = MockUuid("up-the-irons")
    args = [
        'Hello world',
        '--visibility', 'unlisted',
        '--sensitive',
        '--spoiler-text', 'Spoiler!',
        '--reply-to', '123a',
        '--language', 'hr',
    ]

    mock_post.return_value = MockResponse({
        'url': 'https://habunek.com/@ihabunek/1234567890'
    })

    console.run_command(app, user, 'post', args)

    mock_post.assert_called_once_with(app, user, '/api/v1/statuses', json={
        'status': 'Hello world',
        'media_ids': [],
        'visibility': 'unlisted',
        'sensitive': True,
        'spoiler_text': "Spoiler!",
        'in_reply_to_id': '123a',
        'language': 'hr',
    }, headers={"Idempotency-Key": "up-the-irons"})

    out, err = capsys.readouterr()
    assert 'Toot posted' in out
    assert 'https://habunek.com/@ihabunek/1234567890' in out
    assert not err


def test_post_invalid_visibility(capsys):
    args = ['Hello world', '--visibility', 'foo']

    with pytest.raises(SystemExit):
        console.run_command(app, user, 'post', args)

    out, err = capsys.readouterr()
    assert "invalid visibility value: 'foo'" in err


def test_post_invalid_media(capsys):
    args = ['Hello world', '--media', 'does_not_exist.jpg']

    with pytest.raises(SystemExit):
        console.run_command(app, user, 'post', args)

    out, err = capsys.readouterr()
    assert "can't open 'does_not_exist.jpg'" in err


@mock.patch('toot.http.delete')
def test_delete(mock_delete, capsys):
    console.run_command(app, user, 'delete', ['12321'])

    mock_delete.assert_called_once_with(app, user, '/api/v1/statuses/12321')

    out, err = capsys.readouterr()
    assert 'Status deleted' in out
    assert not err


@mock.patch('toot.http.get')
def test_timeline(mock_get, monkeypatch, capsys):
    mock_get.return_value = MockResponse([{
        'id': '111111111111111111',
        'account': {
            'display_name': 'Frank Zappa 🎸',
            'last_status_at': '2017-04-12T15:53:18.174Z',
            'acct': 'fz'
        },
        'created_at': '2017-04-12T15:53:18.174Z',
        'content': "<p>The computer can&apos;t tell you the emotional story. It can give you the exact mathematical design, but what's missing is the eyebrows.</p>",
        'reblog': None,
        'in_reply_to_id': None,
        'media_attachments': [],
    }])

    console.run_command(app, user, 'timeline', ['--once'])

    mock_get.assert_called_once_with(app, user, '/api/v1/timelines/home', {'limit': 10})

    out, err = capsys.readouterr()
    lines = out.split("\n")

    assert "Frank Zappa 🎸" in lines[1]
    assert "@fz" in lines[1]
    assert "2017-04-12 15:53 UTC" in lines[1]

    assert (
        "The computer can't tell you the emotional story. It can give you the "
        "exact mathematical design, but\nwhat's missing is the eyebrows." in out)

    assert "111111111111111111" in lines[-3]

    assert err == ""


@mock.patch('toot.http.get')
def test_timeline_with_re(mock_get, monkeypatch, capsys):
    mock_get.return_value = MockResponse([{
        'id': '111111111111111111',
        'created_at': '2017-04-12T15:53:18.174Z',
        'account': {
            'display_name': 'Frank Zappa',
            'acct': 'fz'
        },
        'reblog': {
            'created_at': '2017-04-12T15:53:18.174Z',
            'account': {
                'display_name': 'Johnny Cash',
                'last_status_at': '2011-04-12',
                'acct': 'jc'
            },
            'content': "<p>The computer can&apos;t tell you the emotional story. It can give you the exact mathematical design, but what's missing is the eyebrows.</p>",
            'media_attachments': [],
        },
        'in_reply_to_id': '111111111111111110',
        'media_attachments': [],
    }])

    console.run_command(app, user, 'timeline', ['--once'])

    mock_get.assert_called_once_with(app, user, '/api/v1/timelines/home', {'limit': 10})

    out, err = capsys.readouterr()
    lines = uncolorize(out).split("\n")

    assert "Johnny Cash" in lines[1]
    assert "@jc" in lines[1]
    assert "2017-04-12 15:53 UTC" in lines[1]

    assert (
        "The computer can't tell you the emotional story. It can give you the "
        "exact mathematical design, but\nwhat's missing is the eyebrows." in out)

    assert "111111111111111111" in lines[-3]
    assert "↻ @fz boosted" in lines[-3]

    assert err == ""


@mock.patch('toot.http.post')
def test_upload(mock_post, capsys):
    mock_post.return_value = MockResponse({
        'id': 123,
        'preview_url': 'https://bigfish.software/789/012',
        'url': 'https://bigfish.software/345/678',
        'type': 'image',
    })

    console.run_command(app, user, 'upload', [__file__])

    assert mock_post.call_count == 1

    args, kwargs = http.post.call_args
    assert args == (app, user, '/api/v2/media')
    assert isinstance(kwargs['files']['file'], io.BufferedReader)

    out, err = capsys.readouterr()
    assert "Uploading media" in out
    assert __file__ in out


@mock.patch('toot.http.get')
def test_whoami(mock_get, capsys):
    mock_get.return_value = MockResponse({
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
        'username': 'ihabunek',
        'fields': []
    })

    console.run_command(app, user, 'whoami', [])

    mock_get.assert_called_once_with(app, user, '/api/v1/accounts/verify_credentials')

    out, err = capsys.readouterr()
    out = uncolorize(out)

    assert "@ihabunek Ivan Habunek" in out
    assert "A developer." in out
    assert "https://mastodon.social/@ihabunek" in out
    assert "ID: 46103" in out
    assert "Since: 2017-04-04" in out
    assert "Followers: 5" in out
    assert "Following: 9" in out
    assert "Statuses: 19" in out


@mock.patch('toot.http.get')
def test_notifications(mock_get, capsys):
    mock_get.return_value = MockResponse([{
        'id': '1',
        'type': 'follow',
        'created_at': '2019-02-16T07:01:20.714Z',
        'account': {
            'display_name': 'Frank Zappa',
            'acct': 'frank@zappa.social',
        },
    }, {
        'id': '2',
        'type': 'mention',
        'created_at': '2017-01-12T12:12:12.0Z',
        'account': {
            'display_name': 'Dweezil Zappa',
            'acct': 'dweezil@zappa.social',
        },
        'status': {
            'id': '111111111111111111',
            'account': {
                'display_name': 'Dweezil Zappa',
                'acct': 'dweezil@zappa.social',
            },
            'created_at': '2017-04-12T15:53:18.174Z',
            'content': "<p>We still have fans in 2017 @fan123</p>",
            'reblog': None,
            'in_reply_to_id': None,
            'media_attachments': [],
        },
    }, {
        'id': '3',
        'type': 'reblog',
        'created_at': '1983-11-03T03:03:03.333Z',
        'account': {
            'display_name': 'Terry Bozzio',
            'acct': 'terry@bozzio.social',
        },
        'status': {
            'id': '1234',
            'account': {
                'display_name': 'Zappa Fan',
                'acct': 'fan123@zappa-fans.social'
            },
            'created_at': '1983-11-04T15:53:18.174Z',
            'content': "<p>The Black Page, a masterpiece</p>",
            'reblog': None,
            'in_reply_to_id': None,
            'media_attachments': [],
        },
    }, {
        'id': '4',
        'type': 'favourite',
        'created_at': '1983-12-13T01:02:03.444Z',
        'account': {
            'display_name': 'Zappa Old Fan',
            'acct': 'fan9@zappa-fans.social',
        },
        'status': {
            'id': '1234',
            'account': {
                'display_name': 'Zappa Fan',
                'acct': 'fan123@zappa-fans.social'
            },
            'created_at': '1983-11-04T15:53:18.174Z',
            'content': "<p>The Black Page, a masterpiece</p>",
            'reblog': None,
            'in_reply_to_id': None,
            'media_attachments': [],
        },
    }])

    console.run_command(app, user, 'notifications', [])

    mock_get.assert_called_once_with(app, user, '/api/v1/notifications', {'exclude_types[]': [], 'limit': 20})

    out, err = capsys.readouterr()
    out = uncolorize(out)

    assert not err
    assert out == "\n".join([
        "────────────────────────────────────────────────────────────────────────────────────────────────────",
        "Frank Zappa @frank@zappa.social now follows you",
        "────────────────────────────────────────────────────────────────────────────────────────────────────",
        "Dweezil Zappa @dweezil@zappa.social mentioned you in",
        "Dweezil Zappa @dweezil@zappa.social                                             2017-04-12 15:53 UTC",
        "",
        "We still have fans in 2017 @fan123",
        "",
        "ID 111111111111111111   ",
        "────────────────────────────────────────────────────────────────────────────────────────────────────",
        "Terry Bozzio @terry@bozzio.social reblogged your status",
        "Zappa Fan @fan123@zappa-fans.social                                             1983-11-04 15:53 UTC",
        "",
        "The Black Page, a masterpiece",
        "",
        "ID 1234   ",
        "────────────────────────────────────────────────────────────────────────────────────────────────────",
        "Zappa Old Fan @fan9@zappa-fans.social favourited your status",
        "Zappa Fan @fan123@zappa-fans.social                                             1983-11-04 15:53 UTC",
        "",
        "The Black Page, a masterpiece",
        "",
        "ID 1234   ",
        "────────────────────────────────────────────────────────────────────────────────────────────────────",
        "",
    ])


@mock.patch('toot.http.get')
def test_notifications_empty(mock_get, capsys):
    mock_get.return_value = MockResponse([])

    console.run_command(app, user, 'notifications', [])

    mock_get.assert_called_once_with(app, user, '/api/v1/notifications', {'exclude_types[]': [], 'limit': 20})

    out, err = capsys.readouterr()
    out = uncolorize(out)

    assert not err
    assert out == "No notification\n"


@mock.patch('toot.http.post')
def test_notifications_clear(mock_post, capsys):
    console.run_command(app, user, 'notifications', ['--clear'])
    out, err = capsys.readouterr()
    out = uncolorize(out)

    mock_post.assert_called_once_with(app, user, '/api/v1/notifications/clear')
    assert not err
    assert out == 'Cleared notifications\n'


def u(user_id, access_token="abc"):
    username, instance = user_id.split("@")
    return {
        "instance": instance,
        "username": username,
        "access_token": access_token,
    }


@mock.patch('toot.config.save_config')
@mock.patch('toot.config.load_config')
def test_logout(mock_load, mock_save, capsys):
    mock_load.return_value = {
        "users": {
            "king@gizzard.social": u("king@gizzard.social"),
            "lizard@wizard.social": u("lizard@wizard.social"),
        },
        "active_user": "king@gizzard.social",
    }

    console.run_command(app, user, "logout", ["king@gizzard.social"])

    mock_save.assert_called_once_with({
        'users': {
            'lizard@wizard.social': u("lizard@wizard.social")
        },
        'active_user': None
    })

    out, err = capsys.readouterr()
    assert "✓ User king@gizzard.social logged out" in out


@mock.patch('toot.config.save_config')
@mock.patch('toot.config.load_config')
def test_activate(mock_load, mock_save, capsys):
    mock_load.return_value = {
        "users": {
            "king@gizzard.social": u("king@gizzard.social"),
            "lizard@wizard.social": u("lizard@wizard.social"),
        },
        "active_user": "king@gizzard.social",
    }

    console.run_command(app, user, "activate", ["lizard@wizard.social"])

    mock_save.assert_called_once_with({
        'users': {
            "king@gizzard.social": u("king@gizzard.social"),
            'lizard@wizard.social': u("lizard@wizard.social")
        },
        'active_user': "lizard@wizard.social"
    })

    out, err = capsys.readouterr()
    assert "✓ User lizard@wizard.social active" in out
