import json

from toot import App, User, api
from toot.entities import Account, Relationship, from_dict


def test_whoami(user: User, run):
    out = run("whoami")
    # TODO: test other fields once updating account is supported
    assert f"@{user.username}" in out


def test_whoami_json(user: User, run):
    out = run("whoami", "--json")
    account = from_dict(Account, json.loads(out))
    assert account.username == user.username


def test_whois(app: App, friend: User, run):
    variants = [
        friend.username,
        f"@{friend.username}",
        f"{friend.username}@{app.instance}",
        f"@{friend.username}@{app.instance}",
    ]

    for username in variants:
        out = run("whois", username)
        assert f"@{friend.username}" in out


def test_following(app: App, user: User, friend: User, friend_id, run):
    # Make sure we're not initally following friend
    api.unfollow(app, user, friend_id)

    out = run("following", user.username)
    assert out == ""

    out = run("follow", friend.username)
    assert out == f"✓ You are now following {friend.username}"

    out = run("following", user.username)
    assert friend.username in out

    # If no account is given defaults to logged in user
    out = run("following")
    assert friend.username in out

    out = run("unfollow", friend.username)
    assert out == f"✓ You are no longer following {friend.username}"

    out = run("following", user.username)
    assert out == ""


def test_following_case_insensitive(user: User, friend: User, run):
    assert friend.username != friend.username.upper()
    out = run("follow", friend.username.upper())
    assert out == f"✓ You are now following {friend.username.upper()}"


def test_following_not_found(run):
    out = run("follow", "bananaman")
    assert out == "Account not found"

    out = run("unfollow", "bananaman")
    assert out == "Account not found"


def test_following_json(app: App, user: User, friend: User, user_id, friend_id, run_json):
    # Make sure we're not initally following friend
    api.unfollow(app, user, friend_id)

    result = run_json("following", user.username, "--json")
    assert result == []

    result = run_json("followers", friend.username, "--json")
    assert result == []

    result = run_json("follow", friend.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.id == friend_id
    assert relationship.following is True

    [result] = run_json("following", user.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.id == friend_id

    # If no account is given defaults to logged in user
    [result] = run_json("following", user.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.id == friend_id

    [result] = run_json("followers", friend.username, "--json")
    assert result["id"] == user_id

    result = run_json("unfollow", friend.username, "--json")
    assert result["id"] == friend_id
    assert result["following"] is False

    result = run_json("following", user.username, "--json")
    assert result == []

    result = run_json("followers", friend.username, "--json")
    assert result == []


def test_mute(app, user, friend, friend_id, run):
    # Make sure we're not initially muting friend
    api.unmute(app, user, friend_id)

    out = run("muted")
    assert out == "No accounts muted"

    out = run("mute", friend.username)
    assert out == f"✓ You have muted {friend.username}"

    out = run("muted")
    assert friend.username in out

    out = run("unmute", friend.username)
    assert out == f"✓ {friend.username} is no longer muted"

    out = run("muted")
    assert out == "No accounts muted"


def test_mute_case_insensitive(friend: User, run):
    out = run("mute", friend.username.upper())
    assert out == f"✓ You have muted {friend.username.upper()}"


def test_mute_not_found(run):
    out = run("mute", "doesnotexistperson")
    assert out == f"Account not found"

    out = run("unmute", "doesnotexistperson")
    assert out == f"Account not found"


def test_mute_json(app: App, user: User, friend: User, run_json, friend_id):
    # Make sure we're not initially muting friend
    api.unmute(app, user, friend_id)

    result = run_json("muted", "--json")
    assert result == []

    result = run_json("mute", friend.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.id == friend_id
    assert relationship.muting is True

    [result] = run_json("muted", "--json")
    account = from_dict(Account, result)
    assert account.id == friend_id

    result = run_json("unmute", friend.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.id == friend_id
    assert relationship.muting is False

    result = run_json("muted", "--json")
    assert result == []


def test_block(app, user, friend, friend_id, run):
    # Make sure we're not initially blocking friend
    api.unblock(app, user, friend_id)

    out = run("blocked")
    assert out == "No accounts blocked"

    out = run("block", friend.username)
    assert out == f"✓ You are now blocking {friend.username}"

    out = run("blocked")
    assert friend.username in out

    out = run("unblock", friend.username)
    assert out == f"✓ {friend.username} is no longer blocked"

    out = run("blocked")
    assert out == "No accounts blocked"


def test_block_case_insensitive(friend: User, run):
    out = run("block", friend.username.upper())
    assert out == f"✓ You are now blocking {friend.username.upper()}"


def test_block_not_found(run):
    out = run("block", "doesnotexistperson")
    assert out == f"Account not found"


def test_block_json(app: App, user: User, friend: User, run_json, friend_id):
    # Make sure we're not initially blocking friend
    api.unblock(app, user, friend_id)

    result = run_json("blocked", "--json")
    assert result == []

    result = run_json("block", friend.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.id == friend_id
    assert relationship.blocking is True

    [result] = run_json("blocked", "--json")
    account = from_dict(Account, result)
    assert account.id == friend_id

    result = run_json("unblock", friend.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.id == friend_id
    assert relationship.blocking is False

    result = run_json("blocked", "--json")
    assert result == []
