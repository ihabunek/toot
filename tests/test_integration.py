"""
This module contains integration tests meant to run against a test Mastodon instance.

You can set up a test instance locally by following this guide:
https://docs.joinmastodon.org/dev/setup/

To enable integration tests, export the following environment variables to match
your test server and database:

```
export TOOT_TEST_HOSTNAME="localhost:3000"
export TOOT_TEST_DATABASE_DSN="dbname=mastodon_development"
```
"""

import os
import psycopg2
import pytest
import re
import time
import uuid

from datetime import datetime, timedelta, timezone
from os import path
from toot import CLIENT_NAME, CLIENT_WEBSITE, api, App, User
from toot.console import run_command
from toot.exceptions import ConsoleError, NotFoundError
from toot.utils import get_text
from unittest import mock

# Host name of a test instance to run integration tests against
# DO NOT USE PUBLIC INSTANCES!!!
HOSTNAME = os.getenv("TOOT_TEST_HOSTNAME")

# Mastodon database name, used to confirm user registration without having to click the link
DATABASE_DSN = os.getenv("TOOT_TEST_DATABASE_DSN")


if not HOSTNAME or not DATABASE_DSN:
    pytest.skip("Skipping integration tests", allow_module_level=True)

# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------


def create_app():
    response = api.create_app(HOSTNAME, scheme="http")
    return App(HOSTNAME, f"http://{HOSTNAME}", response["client_id"], response["client_secret"])


def register_account(app: App):
    username = str(uuid.uuid4())[-10:]
    email = f"{username}@example.com"

    response = api.register_account(app, username, email, "password", "en")
    confirm_user(email)
    return User(app.instance, username, response["access_token"])


def confirm_user(email):
    conn = psycopg2.connect(DATABASE_DSN)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET confirmed_at = now() WHERE email = %s;", (email,))
    conn.commit()


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.fixture(scope="session")
def user(app):
    return register_account(app)


@pytest.fixture(scope="session")
def friend(app):
    return register_account(app)


@pytest.fixture
def run(app, user, capsys):
    def _run(command, *params, as_user=None):
        run_command(app, as_user or user, command, params or [])
        out, err = capsys.readouterr()
        assert err == ""
        return strip_ansi(out)
    return _run


@pytest.fixture
def run_anon(capsys):
    def _run(command, *params):
        run_command(None, None, command, params or [])
        out, err = capsys.readouterr()
        assert err == ""
        return strip_ansi(out)
    return _run

# ------------------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------------------


def test_instance(app, run):
    out = run("instance", "--disable-https")
    assert "Mastodon" in out
    assert app.instance in out
    assert "running Mastodon" in out


def test_instance_anon(app, run_anon):
    out = run_anon("instance", "--disable-https", HOSTNAME)
    assert "Mastodon" in out
    assert app.instance in out
    assert "running Mastodon" in out

    # Need to specify the instance name when running anon
    with pytest.raises(ConsoleError) as exc:
        run_anon("instance")
    assert str(exc.value) == "Please specify instance name."


def test_post(app, user, run):
    text = "i wish i was a #lumberjack"
    out = run("post", text)
    status_id = _posted_status_id(out)

    status = api.fetch_status(app, user, status_id)
    assert text == get_text(status["content"])
    assert status["visibility"] == "public"
    assert status["sensitive"] is False
    assert status["spoiler_text"] == ""

    # Pleroma doesn't return the application
    if status["application"]:
        assert status["application"]["name"] == CLIENT_NAME
        assert status["application"]["website"] == CLIENT_WEBSITE


def test_post_visibility(app, user, run):
    for visibility in ["public", "unlisted", "private", "direct"]:
        out = run("post", "foo", "--visibility", visibility)
        status_id = _posted_status_id(out)
        status = api.fetch_status(app, user, status_id)
        assert status["visibility"] == visibility


def test_post_scheduled_at(app, user, run):
    text = str(uuid.uuid4())
    scheduled_at = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=10)

    out = run("post", text, "--scheduled-at", scheduled_at.isoformat())
    assert "Toot scheduled for" in out

    statuses = api.scheduled_statuses(app, user)
    [status] = [s for s in statuses if s["params"]["text"] == text]
    assert datetime.strptime(status["scheduled_at"], "%Y-%m-%dT%H:%M:%S.%f%z") == scheduled_at


def test_post_scheduled_in(app, user, run):
    text = str(uuid.uuid4())

    variants = [
        ("1 day", timedelta(days=1)),
        ("1 day 6 hours", timedelta(days=1, hours=6)),
        ("1 day 6 hours 13 minutes", timedelta(days=1, hours=6, minutes=13)),
        ("1 day 6 hours 13 minutes 51 second", timedelta(days=1, hours=6, minutes=13, seconds=51)),
        ("2d", timedelta(days=2)),
        ("2d6h", timedelta(days=2, hours=6)),
        ("2d6h13m", timedelta(days=2, hours=6, minutes=13)),
        ("2d6h13m51s", timedelta(days=2, hours=6, minutes=13, seconds=51)),
    ]

    datetimes = []
    for scheduled_in, delta in variants:
        out = run("post", text, "--scheduled-in", scheduled_in)
        dttm = datetime.utcnow() + delta
        assert out.startswith(f"Toot scheduled for: {str(dttm)[:16]}")
        datetimes.append(dttm)

    scheduled = api.scheduled_statuses(app, user)
    scheduled = [s for s in scheduled if s["params"]["text"] == text]
    scheduled = sorted(scheduled, key=lambda s: s["scheduled_at"])
    assert len(scheduled) == 8

    for expected, status in zip(datetimes, scheduled):
        actual = datetime.strptime(status["scheduled_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
        delta = expected - actual
        assert delta.total_seconds() < 5


def test_post_language(app, user, run):
    out = run("post", "test", "--language", "hr")
    status_id = _posted_status_id(out)
    status = api.fetch_status(app, user, status_id)
    assert status["language"] == "hr"

    out = run("post", "test", "--language", "zh")
    status_id = _posted_status_id(out)
    status = api.fetch_status(app, user, status_id)
    assert status["language"] == "zh"


def test_media_attachments(app, user, run):
    assets_dir = path.realpath(path.join(path.dirname(__file__), "assets"))

    path1 = path.join(assets_dir, "test1.png")
    path2 = path.join(assets_dir, "test2.png")
    path3 = path.join(assets_dir, "test3.png")
    path4 = path.join(assets_dir, "test4.png")

    out = run(
        "post",
        "--media", path1,
        "--media", path2,
        "--media", path3,
        "--media", path4,
        "--description", "Test 1",
        "--description", "Test 2",
        "--description", "Test 3",
        "--description", "Test 4",
        "some text"
    )

    status_id = _posted_status_id(out)
    status = api.fetch_status(app, user, status_id)

    [a1, a2, a3, a4] = status["media_attachments"]

    # Pleroma doesn't send metadata
    if "meta" in a1:
        assert a1["meta"]["original"]["size"] == "50x50"
        assert a2["meta"]["original"]["size"] == "50x60"
        assert a3["meta"]["original"]["size"] == "50x70"
        assert a4["meta"]["original"]["size"] == "50x80"

    assert a1["description"] == "Test 1"
    assert a2["description"] == "Test 2"
    assert a3["description"] == "Test 3"
    assert a4["description"] == "Test 4"


@mock.patch("toot.utils.multiline_input")
@mock.patch("sys.stdin.read")
def test_media_attachment_without_text(mock_read, mock_ml, app, user, run):
    # No status from stdin or readline
    mock_read.return_value = ""
    mock_ml.return_value = ""

    assets_dir = path.realpath(path.join(path.dirname(__file__), "assets"))
    media_path = path.join(assets_dir, "test1.png")

    out = run("post", "--media", media_path)
    status_id = _posted_status_id(out)

    status = api.fetch_status(app, user, status_id)
    assert status["content"] == ""

    [attachment] = status["media_attachments"]
    assert not attachment["description"]

    # Pleroma doesn't send metadata
    if "meta" in attachment:
        assert attachment["meta"]["original"]["size"] == "50x50"


def test_delete_status(app, user, run):
    status = api.post_status(app, user, "foo")

    out = run("delete", status["id"])
    assert out == "✓ Status deleted"

    with pytest.raises(NotFoundError):
        api.fetch_status(app, user, status["id"])


def test_reply_thread(app, user, friend, run):
    status = api.post_status(app, friend, "This is the status")

    out = run("post", "--reply-to", status["id"], "This is the reply")
    status_id = _posted_status_id(out)
    reply = api.fetch_status(app, user, status_id)

    assert reply["in_reply_to_id"] == status["id"]

    out = run("thread", status["id"])
    [s1, s2] = [s.strip() for s in re.split(r"─+", out) if s.strip()]

    assert "This is the status" in s1
    assert "This is the reply" in s2
    assert friend.username in s1
    assert user.username in s2
    assert status["id"] in s1
    assert reply["id"] in s2


def test_favourite(app, user, run):
    status = api.post_status(app, user, "foo")
    assert not status["favourited"]

    out = run("favourite", status["id"])
    assert out == "✓ Status favourited"

    status = api.fetch_status(app, user, status["id"])
    assert status["favourited"]

    out = run("unfavourite", status["id"])
    assert out == "✓ Status unfavourited"

    # A short delay is required before the server returns new data
    time.sleep(0.1)

    status = api.fetch_status(app, user, status["id"])
    assert not status["favourited"]


def test_reblog(app, user, run):
    status = api.post_status(app, user, "foo")
    assert not status["reblogged"]

    out = run("reblog", status["id"])
    assert out == "✓ Status reblogged"

    status = api.fetch_status(app, user, status["id"])
    assert status["reblogged"]

    out = run("reblogged_by", status["id"])
    assert out == f"@{user.username}"

    out = run("unreblog", status["id"])
    assert out == "✓ Status unreblogged"

    status = api.fetch_status(app, user, status["id"])
    assert not status["reblogged"]


def test_pin(app, user, run):
    status = api.post_status(app, user, "foo")
    assert not status["pinned"]

    out = run("pin", status["id"])
    assert out == "✓ Status pinned"

    status = api.fetch_status(app, user, status["id"])
    assert status["pinned"]

    out = run("unpin", status["id"])
    assert out == "✓ Status unpinned"

    status = api.fetch_status(app, user, status["id"])
    assert not status["pinned"]


def test_bookmark(app, user, run):
    status = api.post_status(app, user, "foo")
    assert not status["bookmarked"]

    out = run("bookmark", status["id"])
    assert out == "✓ Status bookmarked"

    status = api.fetch_status(app, user, status["id"])
    assert status["bookmarked"]

    out = run("unbookmark", status["id"])
    assert out == "✓ Status unbookmarked"

    status = api.fetch_status(app, user, status["id"])
    assert not status["bookmarked"]


def test_whoami(user, run):
    out = run("whoami")
    # TODO: test other fields once updating account is supported
    assert f"@{user.username}" in out
    assert f"http://{HOSTNAME}/@{user.username}" in out


def test_whois(app, friend, run):
    variants = [
        friend.username,
        f"@{friend.username}",
        f"{friend.username}@{app.instance}",
        f"@{friend.username}@{app.instance}",
    ]

    for username in variants:
        out = run("whois", username)
        assert f"@{friend.username}" in out
        assert f"http://{HOSTNAME}/@{friend.username}" in out


def test_search_account(friend, run):
    out = run("search", friend.username)
    assert out == f"Accounts:\n* @{friend.username}"


def test_search_hashtag(app, user, run):
    api.post_status(app, user, "#hashtag_x")
    api.post_status(app, user, "#hashtag_y")
    api.post_status(app, user, "#hashtag_z")

    out = run("search", "#hashtag")
    assert out == "Hashtags:\n#hashtag_x, #hashtag_y, #hashtag_z"


def test_follow(friend, run):
    out = run("follow", friend.username)
    assert out == f"✓ You are now following {friend.username}"

    out = run("unfollow", friend.username)
    assert out == f"✓ You are no longer following {friend.username}"


def test_follow_case_insensitive(friend, run):
    username = friend.username.upper()

    out = run("follow", username)
    assert out == f"✓ You are now following {username}"

    out = run("unfollow", username)
    assert out == f"✓ You are no longer following {username}"


# TODO: improve testing stderr, catching exceptions is not optimal
def test_follow_not_found(run):
    with pytest.raises(ConsoleError) as ex_info:
        run("follow", "banana")
    assert str(ex_info.value) == "Account not found"


# ------------------------------------------------------------------------------
# Utils
# ------------------------------------------------------------------------------

strip_ansi_pattern = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(string):
    return strip_ansi_pattern.sub("", string).strip()


def _posted_status_id(out):
    pattern = re.compile(r"Toot posted: http://([^/]+)/([^/]+)/(.+)")
    match = re.search(pattern, out)
    assert match

    host, _, status_id = match.groups()
    assert host == HOSTNAME

    return status_id
