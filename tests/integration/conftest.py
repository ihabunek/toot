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

import re
import os
import psycopg2
import pytest
import uuid

from pathlib import Path
from toot import api, App, User
from toot.console import run_command
from toot.exceptions import ApiError, ConsoleError
from toot.output import print_out

# Host name of a test instance to run integration tests against
# DO NOT USE PUBLIC INSTANCES!!!
BASE_URL = os.getenv("TOOT_TEST_BASE_URL")

# Mastodon database name, used to confirm user registration without having to click the link
DATABASE_DSN = os.getenv("TOOT_TEST_DATABASE_DSN")

# Toot logo used for testing image upload
TRUMPET = str(Path(__file__).parent.parent.parent / "trumpet.png")

ASSETS_DIR = str(Path(__file__).parent.parent / "assets")


if not BASE_URL or not DATABASE_DSN:
    pytest.skip("Skipping integration tests", allow_module_level=True)

# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------


def create_app():
    instance = api.get_instance(BASE_URL)
    response = api.create_app(BASE_URL)
    return App(instance["uri"], BASE_URL, response["client_id"], response["client_secret"])


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
        # The try/catch duplicates logic from console.main to convert exceptions
        # to printed error messages. TODO: could be deduped
        try:
            run_command(app, as_user or user, command, params or [])
        except (ConsoleError, ApiError) as e:
            print_out(str(e))

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
# Utils
# ------------------------------------------------------------------------------

strip_ansi_pattern = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(string):
    return strip_ansi_pattern.sub("", string).strip()


def posted_status_id(out):
    pattern = re.compile(r"Toot posted: http://([^/]+)/([^/]+)/(.+)")
    match = re.search(pattern, out)
    assert match

    _, _, status_id = match.groups()

    return status_id
