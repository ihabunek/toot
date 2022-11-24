"""
This module contains integration tests meant to run against a test Mastodon instance.

You can set up a test instance locally by following this guide:
https://docs.joinmastodon.org/dev/setup/

To enable integration tests, export the following environment variables to match
your test server and database:

```
export TOOT_TEST_HOSTNAME="localhost:3000"
export TOOT_TEST_DATABASE_DSN="mastodon_development"
```
"""

import os
import psycopg2
import pytest
import re
import uuid

from os import path
from toot import CLIENT_NAME, CLIENT_WEBSITE, api, App, User
from toot.console import run_command
from toot.exceptions import NotFoundError
from toot.utils import get_text

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


# ------------------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------------------

def test_get_instance(app):
    response = api.get_instance(HOSTNAME, scheme="http")
    assert response["title"] == "Mastodon"
    assert response["uri"] == app.instance


def test_post(app, user, capsys):
    text = "i wish i was a #lumberjack"
    run_command(app, user, "post", [text])
    status_id = _posted_status_id(capsys)

    status = api.fetch_status(app, user, status_id)
    assert text == get_text(status["content"])
    assert status["account"]["acct"] == user.username
    assert status["application"]["name"] == CLIENT_NAME
    assert status["application"]["website"] == CLIENT_WEBSITE
    assert status["visibility"] == "public"
    assert status["sensitive"] is False
    assert status["spoiler_text"] == ""


def test_post_visibility(app, user, capsys):
    for visibility in ["public", "unlisted", "private", "direct"]:
        run_command(app, user, "post", ["foo", "--visibility", visibility])
        status_id = _posted_status_id(capsys)
        status = api.fetch_status(app, user, status_id)
        assert status["visibility"] == visibility


def test_media_attachments(app, user, capsys):
    assets_dir = path.realpath(path.join(path.dirname(__file__), "assets"))

    path1 = path.join(assets_dir, "test1.png")
    path2 = path.join(assets_dir, "test2.png")
    path3 = path.join(assets_dir, "test3.png")
    path4 = path.join(assets_dir, "test4.png")

    run_command(app, user, "post", [
        "--media", path1,
        "--media", path2,
        "--media", path3,
        "--media", path4,
        "--description", "Test 1",
        "--description", "Test 2",
        "--description", "Test 3",
        "--description", "Test 4",
        "some text"
    ])

    status_id = _posted_status_id(capsys)
    status = api.fetch_status(app, user, status_id)

    [a1, a2, a3, a4] = status["media_attachments"]

    assert a1["meta"]["original"]["size"] == "50x50"
    assert a2["meta"]["original"]["size"] == "50x60"
    assert a3["meta"]["original"]["size"] == "50x70"
    assert a4["meta"]["original"]["size"] == "50x80"

    assert a1["description"] == "Test 1"
    assert a2["description"] == "Test 2"
    assert a3["description"] == "Test 3"
    assert a4["description"] == "Test 4"


def test_delete_status(app, user):
    status = api.post_status(app, user, "foo")

    response = api.delete_status(app, user, status["id"]).json()
    assert response["id"] == status["id"]

    with pytest.raises(NotFoundError):
        api.fetch_status(app, user, response["id"])


def test_favourite(app, user, capsys):
    status = api.post_status(app, user, "foo")
    assert not status["favourited"]

    run_command(app, user, "favourite", [status["id"]])

    out, err = capsys.readouterr()
    assert strip_ansi(out) == "✓ Status favourited"
    assert err == ""

    status = api.fetch_status(app, user, status["id"])
    assert status["favourited"]

    run_command(app, user, "unfavourite", [status["id"]])

    out, err = capsys.readouterr()
    assert strip_ansi(out) == "✓ Status unfavourited"
    assert err == ""

    status = api.fetch_status(app, user, status["id"])
    assert not status["favourited"]


def test_reblog(app, user, capsys):
    status = api.post_status(app, user, "foo")
    assert not status["reblogged"]

    run_command(app, user, "reblog", [status["id"]])

    out, err = capsys.readouterr()
    assert strip_ansi(out) == "✓ Status reblogged"
    assert err == ""

    status = api.fetch_status(app, user, status["id"])
    assert status["reblogged"]

    run_command(app, user, "reblogged_by", [status["id"]])

    out, err = capsys.readouterr()
    assert strip_ansi(out) == f"@{user.username}"

    run_command(app, user, "unreblog", [status["id"]])

    out, err = capsys.readouterr()
    assert strip_ansi(out) == "✓ Status unreblogged"
    assert err == ""

    status = api.fetch_status(app, user, status["id"])
    assert not status["reblogged"]


def test_pin(app, user, capsys):
    status = api.post_status(app, user, "foo")
    assert not status["pinned"]

    run_command(app, user, "pin", [status["id"]])

    out, err = capsys.readouterr()
    assert strip_ansi(out) == "✓ Status pinned"
    assert err == ""

    status = api.fetch_status(app, user, status["id"])
    assert status["pinned"]

    run_command(app, user, "unpin", [status["id"]])

    out, err = capsys.readouterr()
    assert strip_ansi(out) == "✓ Status unpinned"
    assert err == ""

    status = api.fetch_status(app, user, status["id"])
    assert not status["pinned"]


def test_bookmark(app, user, capsys):
    status = api.post_status(app, user, "foo")
    assert not status["bookmarked"]

    run_command(app, user, "bookmark", [status["id"]])

    out, err = capsys.readouterr()
    assert strip_ansi(out) == "✓ Status bookmarked"
    assert err == ""

    status = api.fetch_status(app, user, status["id"])
    assert status["bookmarked"]

    run_command(app, user, "unbookmark", [status["id"]])

    out, err = capsys.readouterr()
    assert strip_ansi(out) == "✓ Status unbookmarked"
    assert err == ""

    status = api.fetch_status(app, user, status["id"])
    assert not status["bookmarked"]


# ------------------------------------------------------------------------------
# Utils
# ------------------------------------------------------------------------------

strip_ansi_pattern = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(string):
    return strip_ansi_pattern.sub("", string).strip()


def _posted_status_id(capsys):
    out, err = capsys.readouterr()
    out = strip_ansi(out)
    assert err == ""

    pattern = re.compile(r"Toot posted: http://([^/]+)/@([^/]+)/(.+)")
    match = re.search(pattern, out)
    assert match

    host, _, status_id = match.groups()
    assert host == HOSTNAME

    return status_id
