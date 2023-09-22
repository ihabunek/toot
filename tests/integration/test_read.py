import re
from uuid import uuid4
import pytest

from toot import api
from toot.exceptions import ConsoleError


def test_instance(app, run):
    out = run("instance", "--disable-https")
    assert "Mastodon" in out
    assert app.instance in out
    assert "running Mastodon" in out


def test_instance_anon(app, run_anon, base_url):
    out = run_anon("instance", base_url)
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


def test_tags(run, base_url):
    out = run("tags_followed")
    assert out == "You're not following any hashtags."

    out = run("tags_follow", "foo")
    assert out == "✓ You are now following #foo"

    out = run("tags_followed")
    assert out == f"* #foo\t{base_url}/tags/foo"

    out = run("tags_follow", "bar")
    assert out == "✓ You are now following #bar"

    out = run("tags_followed")
    assert out == "\n".join([
        f"* #bar\t{base_url}/tags/bar",
        f"* #foo\t{base_url}/tags/foo",
    ])

    out = run("tags_unfollow", "foo")
    assert out == "✓ You are no longer following #foo"

    out = run("tags_followed")
    assert out == f"* #bar\t{base_url}/tags/bar"


def test_status(app, user, run):
    uuid = str(uuid4())
    response = api.post_status(app, user, uuid)

    out = run("status", response["id"])
    assert uuid in out
    assert user.username in out
    assert response["id"] in out


def test_thread(app, user, run):
    uuid = str(uuid4())
    s1 = api.post_status(app, user, uuid + "1")
    s2 = api.post_status(app, user, uuid + "2", in_reply_to_id=s1["id"])
    s3 = api.post_status(app, user, uuid + "3", in_reply_to_id=s2["id"])

    for status in [s1, s2, s3]:
        out = run("thread", status["id"])
        bits = re.split(r"─+", out)
        bits = [b for b in bits if b]

        assert len(bits) == 3

        assert s1["id"] in bits[0]
        assert s2["id"] in bits[1]
        assert s3["id"] in bits[2]

        assert f"{uuid}1" in bits[0]
        assert f"{uuid}2" in bits[1]
        assert f"{uuid}3" in bits[2]
