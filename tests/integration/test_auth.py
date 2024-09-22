from typing import Any, Dict
from unittest import mock
from unittest.mock import MagicMock

from toot import User, cli
from tests.integration.conftest import PASSWORD, Run, assert_ok

# TODO: figure out how to test login


EMPTY_CONFIG: Dict[Any, Any] = {
    "apps": {},
    "users": {},
    "active_user": None
}

SAMPLE_CONFIG = {
    "active_user": "frank@foo.social",
    "apps": {
        "foo.social": {
            "base_url": "http://foo.social",
            "client_id": "123",
            "client_secret": "123",
            "instance": "foo.social"
        },
        "bar.social": {
            "base_url": "http://bar.social",
            "client_id": "123",
            "client_secret": "123",
            "instance": "bar.social"
        },
    },
    "users": {
        "frank@foo.social": {
            "access_token": "123",
            "instance": "foo.social",
            "username": "frank"
        },
        "frank@bar.social": {
            "access_token": "123",
            "instance": "bar.social",
            "username": "frank"
        },
    }
}


def test_env(run: Run):
    result = run(cli.auth.env)
    assert_ok(result)
    assert "toot" in result.stdout
    assert "Python" in result.stdout


@mock.patch("toot.config.load_config")
def test_auth_empty(load_config: MagicMock, run: Run):
    load_config.return_value = EMPTY_CONFIG
    result = run(cli.auth.auth)
    assert_ok(result)
    assert result.stdout.strip() == "You are not logged in to any accounts"


@mock.patch("toot.config.load_config")
def test_auth_full(load_config: MagicMock, run: Run):
    load_config.return_value = SAMPLE_CONFIG
    result = run(cli.auth.auth)
    assert_ok(result)
    assert result.stdout.strip().startswith("Authenticated accounts:")
    assert "frank@foo.social" in result.stdout
    assert "frank@bar.social" in result.stdout


# Saving config is mocked so we don't mess up our local config
# TODO: could this be implemented using an auto-use fixture so we have it always
# mocked?
@mock.patch("toot.config.load_app")
@mock.patch("toot.config.save_app")
@mock.patch("toot.config.save_user")
def test_login_cli(
    save_user: MagicMock,
    save_app: MagicMock,
    load_app: MagicMock,
    user: User,
    run: Run,
):
    load_app.return_value = None

    result = run(
        cli.auth.login_cli,
        "--instance", "http://localhost:3000",
        "--email", f"{user.username}@example.com",
        "--password", PASSWORD,
    )
    assert_ok(result)
    assert "✓ Successfully logged in." in result.stdout

    save_app.assert_called_once()
    (app,) = save_app.call_args.args
    assert app.instance == "localhost:3000"
    assert app.base_url == "http://localhost:3000"
    assert app.client_id
    assert app.client_secret

    save_user.assert_called_once()
    (new_user,) = save_user.call_args.args
    assert new_user.instance == "localhost:3000"
    assert new_user.username == user.username
    # access token will be different since this is a new login
    assert new_user.access_token and new_user.access_token != user.access_token
    assert save_user.call_args.kwargs == {"activate": True}


@mock.patch("toot.config.load_app")
@mock.patch("toot.config.save_app")
@mock.patch("toot.config.save_user")
def test_login_cli_wrong_password(
    save_user: MagicMock,
    save_app: MagicMock,
    load_app: MagicMock,
    user: User,
    run: Run,
):
    load_app.return_value = None

    result = run(
        cli.auth.login_cli,
        "--instance", "http://localhost:3000",
        "--email", f"{user.username}@example.com",
        "--password", "wrong password",
    )
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: Login failed"

    save_app.assert_called_once()
    (app,) = save_app.call_args.args
    assert app.instance == "localhost:3000"
    assert app.base_url == "http://localhost:3000"
    assert app.client_id
    assert app.client_secret

    save_user.assert_not_called()


@mock.patch("toot.config.load_config")
@mock.patch("toot.config.delete_user")
def test_logout(delete_user: MagicMock, load_config: MagicMock, run: Run):
    load_config.return_value = SAMPLE_CONFIG

    result = run(cli.auth.logout, "frank@foo.social")
    assert_ok(result)
    assert result.stdout.strip() == "✓ Account frank@foo.social logged out"
    delete_user.assert_called_once_with(User("foo.social", "frank", "123"))


@mock.patch("toot.config.load_config")
def test_logout_not_logged_in(load_config: MagicMock, run: Run):
    load_config.return_value = EMPTY_CONFIG

    result = run(cli.auth.logout)
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: You're not logged into any accounts"


@mock.patch("toot.config.load_config")
def test_logout_account_not_specified(load_config: MagicMock, run: Run):
    load_config.return_value = SAMPLE_CONFIG

    result = run(cli.auth.logout)
    assert result.exit_code == 1
    assert result.stderr.startswith("Error: Specify account to log out")


@mock.patch("toot.config.load_config")
def test_logout_account_does_not_exist(load_config: MagicMock, run: Run):
    load_config.return_value = SAMPLE_CONFIG

    result = run(cli.auth.logout, "banana")
    assert result.exit_code == 1
    assert result.stderr.startswith("Error: Account not found")


@mock.patch("toot.config.load_config")
@mock.patch("toot.config.activate_user")
def test_activate(activate_user: MagicMock, load_config: MagicMock, run: Run):
    load_config.return_value = SAMPLE_CONFIG

    result = run(cli.auth.activate, "frank@foo.social")
    assert_ok(result)
    assert result.stdout.strip() == "✓ Account frank@foo.social activated"
    activate_user.assert_called_once_with(User("foo.social", "frank", "123"))


@mock.patch("toot.config.load_config")
def test_activate_not_logged_in(load_config: MagicMock, run: Run):
    load_config.return_value = EMPTY_CONFIG

    result = run(cli.auth.activate)
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: You're not logged into any accounts"


@mock.patch("toot.config.load_config")
def test_activate_account_not_given(load_config: MagicMock, run: Run):
    load_config.return_value = SAMPLE_CONFIG

    result = run(cli.auth.activate)
    assert result.exit_code == 1
    assert result.stderr.startswith("Error: Specify account to activate")


@mock.patch("toot.config.load_config")
def test_activate_invalid_Account(load_config: MagicMock, run: Run):
    load_config.return_value = SAMPLE_CONFIG

    result = run(cli.auth.activate, "banana")
    assert result.exit_code == 1
    assert result.stderr.startswith("Error: Account not found")
