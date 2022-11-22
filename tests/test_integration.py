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


def test_delete_status(app, user):
    status = api.post_status(app, user, "foo")

    response = api.delete_status(app, user, status["id"]).json()
    assert response["id"] == status["id"]

    with pytest.raises(NotFoundError):
        api.fetch_status(app, user, response["id"])


# ------------------------------------------------------------------------------
# Utils
# ------------------------------------------------------------------------------

strip_ansi_pattern = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(string):
    return strip_ansi_pattern.sub("", string)


def _posted_status_id(capsys):
    out, err = capsys.readouterr()
    out = strip_ansi(out)
    assert err == ""

    pattern = re.compile(r"^Toot posted: http://([^/]+)/@([^/]+)/(.+)")
    match = re.match(pattern, out)
    assert match

    host, _, status_id = match.groups()
    assert host == HOSTNAME

    return status_id
