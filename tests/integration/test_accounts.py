import json
from tests.integration.conftest import assert_ok, register_account

from toot import App, User, api, cli
from toot.entities import Account, Relationship, from_dict


def test_whoami(user: User, run):
    result = run(cli.read.whoami)
    assert_ok(result)

    # TODO: test other fields once updating account is supported
    out = result.stdout.strip()
    assert f"@{user.username}" in out


def test_whoami_json(user: User, run):
    result = run(cli.read.whoami, "--json")
    assert_ok(result)

    account = from_dict(Account, json.loads(result.stdout))
    assert account.username == user.username


def test_whois(app: App, friend: User, run):
    variants = [
        friend.username,
        f"@{friend.username}",
        f"{friend.username}@{app.instance}",
        f"@{friend.username}@{app.instance}",
    ]

    for username in variants:
        result = run(cli.read.whois, username)
        assert_ok(result)
        assert f"@{friend.username}" in result.stdout


def test_following(app: App, user: User, run):
    friend = register_account(app)

    result = run(cli.accounts.following, user.username)
    assert_ok(result)
    assert result.stdout.strip() == ""

    result = run(cli.accounts.follow, friend.username)
    assert_ok(result)
    assert result.stdout.strip() == f"✓ You are now following {friend.username}"

    result = run(cli.accounts.following, user.username)
    assert_ok(result)
    assert friend.username in result.stdout.strip()

    # If no account is given defaults to logged in user
    result = run(cli.accounts.following)
    assert_ok(result)
    assert friend.username in result.stdout.strip()

    result = run(cli.accounts.unfollow, friend.username)
    assert_ok(result)
    assert result.stdout.strip() == f"✓ You are no longer following {friend.username}"

    result = run(cli.accounts.following, user.username)
    assert_ok(result)
    assert result.stdout.strip() == ""


def test_following_case_insensitive(user: User, friend: User, run):
    assert friend.username != friend.username.upper()
    result = run(cli.accounts.follow, friend.username.upper())
    assert_ok(result)

    out = result.stdout.strip()
    assert out == f"✓ You are now following {friend.username.upper()}"


def test_following_not_found(run):
    result = run(cli.accounts.follow, "bananaman")
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: Account not found"

    result = run(cli.accounts.unfollow, "bananaman")
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: Account not found"


def test_following_json(app: App, user: User, run_json):
    friend = register_account(app)

    result = run_json(cli.accounts.following, user.username, "--json")
    assert result == []

    result = run_json(cli.accounts.followers, friend.username, "--json")
    assert result == []

    result = run_json(cli.accounts.follow, friend.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.following is True

    [result] = run_json(cli.accounts.following, user.username, "--json")
    account = from_dict(Account, result)
    assert account.acct == friend.username

    # If no account is given defaults to logged in user
    [result] = run_json(cli.accounts.following, "--json")
    account = from_dict(Account, result)
    assert account.acct == friend.username

    assert relationship.following is True

    [result] = run_json(cli.accounts.followers, friend.username, "--json")
    account = from_dict(Account, result)
    assert account.acct == user.username

    result = run_json(cli.accounts.unfollow, friend.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.following is False

    result = run_json(cli.accounts.following, user.username, "--json")
    assert result == []

    result = run_json(cli.accounts.followers, friend.username, "--json")
    assert result == []


def test_mute(app, user, friend, friend_id, run):
    # Make sure we're not initially muting friend
    api.unmute(app, user, friend_id)

    result = run(cli.accounts.muted)
    assert_ok(result)

    out = result.stdout.strip()
    assert out == "No accounts muted"

    result = run(cli.accounts.mute, friend.username)
    assert_ok(result)

    out = result.stdout.strip()
    assert out == f"✓ You have muted {friend.username}"

    result = run(cli.accounts.muted)
    assert_ok(result)

    out = result.stdout.strip()
    assert friend.username in out

    result = run(cli.accounts.unmute, friend.username)
    assert_ok(result)

    out = result.stdout.strip()
    assert out == f"✓ {friend.username} is no longer muted"

    result = run(cli.accounts.muted)
    assert_ok(result)

    out = result.stdout.strip()
    assert out == "No accounts muted"


def test_mute_case_insensitive(friend: User, run):
    result = run(cli.accounts.mute, friend.username.upper())
    assert_ok(result)

    out = result.stdout.strip()
    assert out == f"✓ You have muted {friend.username.upper()}"


def test_mute_not_found(run):
    result = run(cli.accounts.mute, "doesnotexistperson")
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: Account not found"

    result = run(cli.accounts.unmute, "doesnotexistperson")
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: Account not found"


def test_mute_json(app: App, user: User, friend: User, run_json, friend_id):
    # Make sure we're not initially muting friend
    api.unmute(app, user, friend_id)

    result = run_json(cli.accounts.muted, "--json")
    assert result == []

    result = run_json(cli.accounts.mute, friend.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.id == friend_id
    assert relationship.muting is True

    [result] = run_json(cli.accounts.muted, "--json")
    account = from_dict(Account, result)
    assert account.id == friend_id

    result = run_json(cli.accounts.unmute, friend.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.id == friend_id
    assert relationship.muting is False

    result = run_json(cli.accounts.muted, "--json")
    assert result == []


def test_block(app, user, run):
    friend = register_account(app)

    result = run(cli.accounts.blocked)
    assert_ok(result)

    out = result.stdout.strip()
    assert out == "No accounts blocked"

    result = run(cli.accounts.block, friend.username)
    assert_ok(result)

    out = result.stdout.strip()
    assert out == f"✓ You are now blocking {friend.username}"

    result = run(cli.accounts.blocked)
    assert_ok(result)

    out = result.stdout.strip()
    assert friend.username in out

    result = run(cli.accounts.unblock, friend.username)
    assert_ok(result)

    out = result.stdout.strip()
    assert out == f"✓ {friend.username} is no longer blocked"

    result = run(cli.accounts.blocked)
    assert_ok(result)

    out = result.stdout.strip()
    assert out == "No accounts blocked"


def test_block_case_insensitive(friend: User, run):
    result = run(cli.accounts.block, friend.username.upper())
    assert_ok(result)

    out = result.stdout.strip()
    assert out == f"✓ You are now blocking {friend.username.upper()}"


def test_block_not_found(run):
    result = run(cli.accounts.block, "doesnotexistperson")
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: Account not found"


def test_block_json(app: App, user: User, friend: User, run_json, friend_id):
    # Make sure we're not initially blocking friend
    api.unblock(app, user, friend_id)

    result = run_json(cli.accounts.blocked, "--json")
    assert result == []

    result = run_json(cli.accounts.block, friend.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.id == friend_id
    assert relationship.blocking is True

    [result] = run_json(cli.accounts.blocked, "--json")
    account = from_dict(Account, result)
    assert account.id == friend_id

    result = run_json(cli.accounts.unblock, friend.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.id == friend_id
    assert relationship.blocking is False

    result = run_json(cli.accounts.blocked, "--json")
    assert result == []
