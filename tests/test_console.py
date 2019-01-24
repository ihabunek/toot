# -*- coding: utf-8 -*-
import io
import pytest
import re
import uuid

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

    mock_post.assert_called_once_with(app, user, '/api/v1/statuses', {
        'status': 'Hello world',
        'visibility': 'public',
        'media_ids[]': None,
        'sensitive': "false",
        'spoiler_text': None,
        'in_reply_to_id': None,
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
        '--reply-to', '123'
    ]

    mock_post.return_value = MockResponse({
        'url': 'https://habunek.com/@ihabunek/1234567890'
    })

    console.run_command(app, user, 'post', args)

    mock_post.assert_called_once_with(app, user, '/api/v1/statuses', {
        'status': 'Hello world',
        'media_ids[]': None,
        'visibility': 'unlisted',
        'sensitive': "true",
        'spoiler_text': "Spoiler!",
        'in_reply_to_id': 123,
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
            'display_name': 'Frank Zappa',
            'username': 'fz'
        },
        'created_at': '2017-04-12T15:53:18.174Z',
        'content': "<p>The computer can&apos;t tell you the emotional story. It can give you the exact mathematical design, but what's missing is the eyebrows.</p>",
        'reblog': None,
        'in_reply_to_id': None
    }])

    console.run_command(app, user, 'timeline', [])

    mock_get.assert_called_once_with(app, user, '/api/v1/timelines/home')

    out, err = capsys.readouterr()
    assert "The computer can't tell you the emotional story." in out
    assert "but what's missing is the eyebrows." in out
    assert "Frank Zappa" in out
    assert "@fz" in out
    assert "id: 111111111111111111" in out
    assert "[RE]" not in out

@mock.patch('toot.http.get')
def test_timeline_with_re(mock_get, monkeypatch, capsys):
    mock_get.return_value = MockResponse([{
        'id': '111111111111111111',
        'account': {
            'display_name': 'Frank Zappa',
            'username': 'fz'
        },
        'created_at': '2017-04-12T15:53:18.174Z',
        'content': "<p>The computer can&apos;t tell you the emotional story. It can give you the exact mathematical design, but what's missing is the eyebrows.</p>",
        'reblog': None,
        'in_reply_to_id': '111111111111111110'
    }])

    console.run_command(app, user, 'timeline', [])

    mock_get.assert_called_once_with(app, user, '/api/v1/timelines/home')

    out, err = capsys.readouterr()
    assert "The computer can't tell you the emotional story." in out
    assert "but what's missing is the eyebrows." in out
    assert "Frank Zappa" in out
    assert "@fz" in out
    assert "id: 111111111111111111" in out
    assert "[RE]" in out

@mock.patch('toot.http.get')
def test_thread(mock_get, monkeypatch, capsys):
    mock_get.side_effect = [
        MockResponse({
            'id': '111111111111111111',
            'account': {
                'display_name': 'Frank Zappa',
                'username': 'fz'
            },
            'created_at': '2017-04-12T15:53:18.174Z',
            'content': "my response in the middle",
            'reblog': None,
            'in_reply_to_id': '111111111111111110'
        }),
        MockResponse({
            'ancestors': [{
                'id': '111111111111111110',
                'account': {
                    'display_name': 'Frank Zappa',
                    'username': 'fz'
                },
                'created_at': '2017-04-12T15:53:18.174Z',
                'content': "original content",
                'reblog': None,
                'in_reply_to_id': None}],
            'descendants': [{
                'id': '111111111111111112',
                'account': {
                    'display_name': 'Frank Zappa',
                    'username': 'fz'
                },
                'created_at': '2017-04-12T15:53:18.174Z',
                'content': "response message",
                'reblog': None,
                'in_reply_to_id': '111111111111111111'}],
        }),
    ]

    console.run_command(app, user, 'thread', ['111111111111111111'])

    calls = [
        mock.call(app, user, '/api/v1/statuses/111111111111111111'),
        mock.call(app, user, '/api/v1/statuses/111111111111111111/context'),
    ]
    mock_get.assert_has_calls(calls, any_order=False)

    out, err = capsys.readouterr()

    # Display order
    assert out.index('original content') < out.index('my response in the middle')
    assert out.index('my response in the middle') < out.index('response message')

    assert "original content" in out
    assert "my response in the middle" in out
    assert "response message" in out
    assert "Frank Zappa" in out
    assert "@fz" in out
    assert "id: 111111111111111111" in out
    assert "[RE]" in out

@mock.patch('toot.http.get')
def test_reblogged_by(mock_get, monkeypatch, capsys):
    mock_get.return_value = MockResponse([{
        'display_name': 'Terry Bozzio',
        'acct': 'bozzio@drummers.social',
    }, {
        'display_name': 'Dweezil',
        'acct': 'dweezil@zappafamily.social',
    }])

    console.run_command(app, user, 'reblogged_by', ['111111111111111111'])

    calls = [
        mock.call(app, user, '/api/v1/statuses/111111111111111111/reblogged_by'),
    ]
    mock_get.assert_has_calls(calls, any_order=False)

    out, err = capsys.readouterr()

    # Display order
    expected = "\n".join([
        "Terry Bozzio",
        " @bozzio@drummers.social",
        "Dweezil",
        " @dweezil@zappafamily.social",
        "",
    ])
    assert out == expected

@mock.patch('toot.http.post')
def test_upload(mock_post, capsys):
    mock_post.return_value = MockResponse({
        'id': 123,
        'url': 'https://bigfish.software/123/456',
        'preview_url': 'https://bigfish.software/789/012',
        'text_url': 'https://bigfish.software/345/678',
        'type': 'image',
    })

    console.run_command(app, user, 'upload', [__file__])

    mock_post.call_count == 1

    args, kwargs = http.post.call_args
    assert args == (app, user, '/api/v1/media')
    assert isinstance(kwargs['files']['file'], io.BufferedReader)

    out, err = capsys.readouterr()
    assert "Uploading media" in out
    assert __file__ in out


@mock.patch('toot.http.get')
def test_search(mock_get, capsys):
    mock_get.return_value = MockResponse({
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

    console.run_command(app, user, 'search', ['freddy'])

    mock_get.assert_called_once_with(app, user, '/api/v1/search', {
        'q': 'freddy',
        'resolve': False,
    })

    out, err = capsys.readouterr()
    assert "Hashtags:\n\033[32m#foo\033[0m, \033[32m#bar\033[0m, \033[32m#baz\033[0m" in out
    assert "Accounts:" in out
    assert "\033[32m@thequeen\033[0m Freddy Mercury" in out
    assert "\033[32m@thequeen@other.instance\033[0m Mercury Freddy" in out


@mock.patch('toot.http.post')
@mock.patch('toot.http.get')
def test_follow(mock_get, mock_post, capsys):
    mock_get.return_value = MockResponse([
        {'id': 123, 'acct': 'blixa@other.acc'},
        {'id': 321, 'acct': 'blixa'},
    ])
    mock_post.return_value = MockResponse()

    console.run_command(app, user, 'follow', ['blixa'])

    mock_get.assert_called_once_with(app, user, '/api/v1/accounts/search', {'q': 'blixa'})
    mock_post.assert_called_once_with(app, user, '/api/v1/accounts/321/follow')

    out, err = capsys.readouterr()
    assert "You are now following blixa" in out


@mock.patch('toot.http.get')
def test_follow_not_found(mock_get, capsys):
    mock_get.return_value = MockResponse()

    with pytest.raises(ConsoleError) as ex:
        console.run_command(app, user, 'follow', ['blixa'])

    mock_get.assert_called_once_with(app, user, '/api/v1/accounts/search', {'q': 'blixa'})
    assert "Account not found" == str(ex.value)


@mock.patch('toot.http.post')
@mock.patch('toot.http.get')
def test_unfollow(mock_get, mock_post, capsys):
    mock_get.return_value = MockResponse([
        {'id': 123, 'acct': 'blixa@other.acc'},
        {'id': 321, 'acct': 'blixa'},
    ])

    mock_post.return_value = MockResponse()

    console.run_command(app, user, 'unfollow', ['blixa'])

    mock_get.assert_called_once_with(app, user, '/api/v1/accounts/search', {'q': 'blixa'})
    mock_post.assert_called_once_with(app, user, '/api/v1/accounts/321/unfollow')

    out, err = capsys.readouterr()
    assert "You are no longer following blixa" in out


@mock.patch('toot.http.get')
def test_unfollow_not_found(mock_get, capsys):
    mock_get.return_value = MockResponse([])

    with pytest.raises(ConsoleError) as ex:
        console.run_command(app, user, 'unfollow', ['blixa'])

    mock_get.assert_called_once_with(app, user, '/api/v1/accounts/search', {'q': 'blixa'})

    assert "Account not found" == str(ex.value)


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
        'username': 'ihabunek'
    })

    console.run_command(app, user, 'whoami', [])

    mock_get.assert_called_once_with(app, user, '/api/v1/accounts/verify_credentials')

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
