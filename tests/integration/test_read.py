import pytest

from tests.integration.conftest import BASE_URL
from toot import api
from toot.exceptions import ConsoleError


def test_instance(app, run):
    out = run("instance", "--disable-https")
    assert "Mastodon" in out
    assert app.instance in out
    assert "running Mastodon" in out


def test_instance_anon(app, run_anon):
    out = run_anon("instance", BASE_URL)
    assert "Mastodon" in out
    assert app.instance in out
    assert "running Mastodon" in out

    # Need to specify the instance name when running anon
    with pytest.raises(ConsoleError) as exc:
        run_anon("instance")
    assert str(exc.value) == "Please specify an instance."


def test_whoami(user, run):
    out = run("whoami")
    # TODO: test other fields once updating account is supported
    assert f"@{user.username}" in out


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


def test_search_account(friend, run):
    out = run("search", friend.username)
    assert out == f"Accounts:\n* @{friend.username}"


def test_search_hashtag(app, user, run):
    api.post_status(app, user, "#hashtag_x")
    api.post_status(app, user, "#hashtag_y")
    api.post_status(app, user, "#hashtag_z")

    out = run("search", "#hashtag")
    assert out == "Hashtags:\n#hashtag_x, #hashtag_y, #hashtag_z"


def test_tags(run):
    out = run("tags_followed")
    assert out == "You're not following any hashtags."

    out = run("tags_follow", "foo")
    assert out == "✓ You are now following #foo"

    out = run("tags_followed")
    assert out == f"* #foo\t{BASE_URL}/tags/foo"

    out = run("tags_follow", "bar")
    assert out == "✓ You are now following #bar"

    out = run("tags_followed")
    assert out == "\n".join([
        f"* #bar\t{BASE_URL}/tags/bar",
        f"* #foo\t{BASE_URL}/tags/foo",
    ])

    out = run("tags_unfollow", "foo")
    assert out == "✓ You are no longer following #foo"

    out = run("tags_followed")
    assert out == f"* #bar\t{BASE_URL}/tags/bar"
