"""
This module contains integration tests meant to run against a test Mastodon instance.

You can set up a test instance locally by following this guide:
https://docs.joinmastodon.org/dev/setup/

To enable integration tests, export the following environment variables to match
your test server and database:

```
export TOOT_TEST_BASE_URL="localhost:3000"
```
"""

import json
import os
import pytest
import re
import typing as t
import uuid

from click.testing import CliRunner, Result
from pathlib import Path
from toot import api, App, User
from toot.cli import Context, TootObj


def pytest_configure(config):
    import toot.settings
    toot.settings.DISABLE_SETTINGS = True


# Type alias for run commands
Run = t.Callable[..., Result]

# Mastodon database name, used to confirm user registration without having to click the link
TOOT_TEST_BASE_URL = os.getenv("TOOT_TEST_BASE_URL")

# Toot logo used for testing image upload
TRUMPET = str(Path(__file__).parent.parent.parent / "trumpet.png")

ASSETS_DIR = str(Path(__file__).parent.parent / "assets")

PASSWORD = "83dU29170rjKilKQQwuWhJv3PKnSW59bWx0perjP6i7Nu4rkeh4mRfYuvVLYM3fM"


def create_app(base_url):
    instance = api.get_instance(base_url).json()
    response = api.create_app(base_url)
    return App(instance["uri"], base_url, response["client_id"], response["client_secret"])


def register_account(app: App):
    username = str(uuid.uuid4())[-10:]
    email = f"{username}@example.com"

    response = api.register_account(app, username, email, PASSWORD, "en")
    return User(app.instance, username, response["access_token"])


# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------


# Host name of a test instance to run integration tests against
# DO NOT USE PUBLIC INSTANCES!!!
@pytest.fixture(scope="session")
def base_url():
    if not TOOT_TEST_BASE_URL:
        pytest.skip("Skipping integration tests, TOOT_TEST_BASE_URL not set")

    return TOOT_TEST_BASE_URL


@pytest.fixture(scope="session")
def app(base_url):
    return create_app(base_url)


@pytest.fixture(scope="session")
def user(app):
    return register_account(app)


@pytest.fixture(scope="session")
def friend(app):
    return register_account(app)


@pytest.fixture(scope="session")
def user_id(app, user):
    return api.find_account(app, user, user.username)["id"]


@pytest.fixture(scope="session")
def friend_id(app, user, friend):
    return api.find_account(app, user, friend.username)["id"]


@pytest.fixture(scope="session", autouse=True)
def testing_env():
    os.environ["TOOT_TESTING"] = "true"


@pytest.fixture(scope="session")
def runner():
    return CliRunner(mix_stderr=False)


@pytest.fixture
def run(app, user, runner):
    def _run(command, *params, input=None) -> Result:
        obj = TootObj(test_ctx=Context(app, user))
        return runner.invoke(command, params, obj=obj, input=input)
    return _run


@pytest.fixture
def run_as(app, runner):
    def _run_as(user, command, *params, input=None) -> Result:
        obj = TootObj(test_ctx=Context(app, user))
        return runner.invoke(command, params, obj=obj, input=input)
    return _run_as


@pytest.fixture
def run_json(app, user, runner):
    def _run_json(command, *params):
        obj = TootObj(test_ctx=Context(app, user))
        result = runner.invoke(command, params, obj=obj)
        assert_ok(result)
        return json.loads(result.stdout)
    return _run_json


@pytest.fixture
def run_anon(runner):
    def _run(command, *params) -> Result:
        obj = TootObj(test_ctx=Context(None, None))
        return runner.invoke(command, params, obj=obj)
    return _run


# ------------------------------------------------------------------------------
# Utils
# ------------------------------------------------------------------------------


def posted_status_id(out):
    pattern = re.compile(r"Toot posted: http://([^/]+)/([^/]+)/(.+)")
    match = re.search(pattern, out)
    assert match

    _, _, status_id = match.groups()

    return status_id


def assert_ok(result: Result):
    if result.exit_code != 0:
        raise AssertionError(f"Command failed with exit code {result.exit_code}\nStderr: {result.stderr}")
