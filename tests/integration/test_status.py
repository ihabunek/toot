import time
import pytest

from toot import api
from toot.exceptions import NotFoundError


def test_delete_status(app, user, run):
    status = api.post_status(app, user, "foo")

    out = run("delete", status["id"])
    assert out == "✓ Status deleted"

    with pytest.raises(NotFoundError):
        api.fetch_status(app, user, status["id"])


def test_favourite(app, user, run):
    status = api.post_status(app, user, "foo")
    assert not status["favourited"]

    out = run("favourite", status["id"])
    assert out == "✓ Status favourited"

    status = api.fetch_status(app, user, status["id"])
    assert status["favourited"]

    out = run("unfavourite", status["id"])
    assert out == "✓ Status unfavourited"

    # A short delay is required before the server returns new data
    time.sleep(0.1)

    status = api.fetch_status(app, user, status["id"])
    assert not status["favourited"]


def test_reblog(app, user, run):
    status = api.post_status(app, user, "foo")
    assert not status["reblogged"]

    out = run("reblog", status["id"])
    assert out == "✓ Status reblogged"

    status = api.fetch_status(app, user, status["id"])
    assert status["reblogged"]

    out = run("reblogged_by", status["id"])
    assert user.username in out

    out = run("unreblog", status["id"])
    assert out == "✓ Status unreblogged"

    status = api.fetch_status(app, user, status["id"])
    assert not status["reblogged"]


def test_pin(app, user, run):
    status = api.post_status(app, user, "foo")
    assert not status["pinned"]

    out = run("pin", status["id"])
    assert out == "✓ Status pinned"

    status = api.fetch_status(app, user, status["id"])
    assert status["pinned"]

    out = run("unpin", status["id"])
    assert out == "✓ Status unpinned"

    status = api.fetch_status(app, user, status["id"])
    assert not status["pinned"]


def test_bookmark(app, user, run):
    status = api.post_status(app, user, "foo")
    assert not status["bookmarked"]

    out = run("bookmark", status["id"])
    assert out == "✓ Status bookmarked"

    status = api.fetch_status(app, user, status["id"])
    assert status["bookmarked"]

    out = run("unbookmark", status["id"])
    assert out == "✓ Status unbookmarked"

    status = api.fetch_status(app, user, status["id"])
    assert not status["bookmarked"]
