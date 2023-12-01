import json
import time
import pytest

from toot import api
from toot.exceptions import NotFoundError


def test_delete(app, user, run):
    status = api.post_status(app, user, "foo").json()

    out = run("delete", status["id"])
    assert out == "✓ Status deleted"

    with pytest.raises(NotFoundError):
        api.fetch_status(app, user, status["id"])


def test_delete_json(app, user, run):
    status = api.post_status(app, user, "foo").json()

    out = run("delete", status["id"], "--json")
    result = json.loads(out)
    assert result["id"] == status["id"]

    with pytest.raises(NotFoundError):
        api.fetch_status(app, user, status["id"])


def test_favourite(app, user, run):
    status = api.post_status(app, user, "foo").json()
    assert not status["favourited"]

    out = run("favourite", status["id"])
    assert out == "✓ Status favourited"

    status = api.fetch_status(app, user, status["id"]).json()
    assert status["favourited"]

    out = run("unfavourite", status["id"])
    assert out == "✓ Status unfavourited"

    # A short delay is required before the server returns new data
    time.sleep(0.1)

    status = api.fetch_status(app, user, status["id"]).json()
    assert not status["favourited"]


def test_favourite_json(app, user, run):
    status = api.post_status(app, user, "foo").json()
    assert not status["favourited"]

    out = run("favourite", status["id"], "--json")
    result = json.loads(out)

    assert result["id"] == status["id"]
    assert result["favourited"] is True

    out = run("unfavourite", status["id"], "--json")
    result = json.loads(out)

    assert result["id"] == status["id"]
    assert result["favourited"] is False


def test_reblog(app, user, run):
    status = api.post_status(app, user, "foo").json()
    assert not status["reblogged"]

    out = run("reblog", status["id"])
    assert out == "✓ Status reblogged"

    status = api.fetch_status(app, user, status["id"]).json()
    assert status["reblogged"]

    out = run("reblogged_by", status["id"])
    assert user.username in out

    out = run("unreblog", status["id"])
    assert out == "✓ Status unreblogged"

    status = api.fetch_status(app, user, status["id"]).json()
    assert not status["reblogged"]


def test_reblog_json(app, user, run):
    status = api.post_status(app, user, "foo").json()
    assert not status["reblogged"]

    out = run("reblog", status["id"], "--json")
    result = json.loads(out)

    assert result["reblogged"] is True
    assert result["reblog"]["id"] == status["id"]

    out = run("reblogged_by", status["id"], "--json")
    [reblog] = json.loads(out)
    assert reblog["acct"] == user.username

    out = run("unreblog", status["id"], "--json")
    result = json.loads(out)

    assert result["reblogged"] is False
    assert result["reblog"] is None


def test_pin(app, user, run):
    status = api.post_status(app, user, "foo").json()
    assert not status["pinned"]

    out = run("pin", status["id"])
    assert out == "✓ Status pinned"

    status = api.fetch_status(app, user, status["id"]).json()
    assert status["pinned"]

    out = run("unpin", status["id"])
    assert out == "✓ Status unpinned"

    status = api.fetch_status(app, user, status["id"]).json()
    assert not status["pinned"]


def test_pin_json(app, user, run):
    status = api.post_status(app, user, "foo").json()
    assert not status["pinned"]

    out = run("pin", status["id"], "--json")
    result = json.loads(out)

    assert result["pinned"] is True
    assert result["id"] == status["id"]

    out = run("unpin", status["id"], "--json")
    result = json.loads(out)

    assert result["pinned"] is False
    assert result["id"] == status["id"]


def test_bookmark(app, user, run):
    status = api.post_status(app, user, "foo").json()
    assert not status["bookmarked"]

    out = run("bookmark", status["id"])
    assert out == "✓ Status bookmarked"

    status = api.fetch_status(app, user, status["id"]).json()
    assert status["bookmarked"]

    out = run("unbookmark", status["id"])
    assert out == "✓ Status unbookmarked"

    status = api.fetch_status(app, user, status["id"]).json()
    assert not status["bookmarked"]


def test_bookmark_json(app, user, run):
    status = api.post_status(app, user, "foo").json()
    assert not status["bookmarked"]

    out = run("bookmark", status["id"], "--json")
    result = json.loads(out)

    assert result["id"] == status["id"]
    assert result["bookmarked"] is True

    out = run("unbookmark", status["id"], "--json")
    result = json.loads(out)

    assert result["id"] == status["id"]
    assert result["bookmarked"] is False
