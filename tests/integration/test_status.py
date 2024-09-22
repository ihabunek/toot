import json
import pytest

from tests.integration.conftest import assert_ok
from tests.utils import run_with_retries
from toot import api, cli
from toot.exceptions import NotFoundError


def test_delete(app, user, run):
    status = api.post_status(app, user, "foo").json()

    result = run(cli.statuses.delete, status["id"])
    assert_ok(result)
    assert result.stdout.strip() == "✓ Status deleted"

    with pytest.raises(NotFoundError):
        api.fetch_status(app, user, status["id"])


def test_delete_json(app, user, run):
    status = api.post_status(app, user, "foo").json()

    result = run(cli.statuses.delete, status["id"], "--json")
    assert_ok(result)

    out = result.stdout
    result = json.loads(out)
    assert result["id"] == status["id"]

    with pytest.raises(NotFoundError):
        api.fetch_status(app, user, status["id"])


def test_favourite(app, user, run):
    status = api.post_status(app, user, "foo").json()
    assert not status["favourited"]

    result = run(cli.statuses.favourite, status["id"])
    assert_ok(result)
    assert result.stdout.strip() == "✓ Status favourited"

    status = api.fetch_status(app, user, status["id"]).json()
    assert status["favourited"]

    result = run(cli.statuses.unfavourite, status["id"])
    assert_ok(result)
    assert result.stdout.strip() == "✓ Status unfavourited"

    def test_favourited():
        nonlocal status
        status = api.fetch_status(app, user, status["id"]).json()
        assert not status["favourited"]
    run_with_retries(test_favourited)


def test_favourite_json(app, user, run):
    status = api.post_status(app, user, "foo").json()
    assert not status["favourited"]

    result = run(cli.statuses.favourite, status["id"], "--json")
    assert_ok(result)

    result = json.loads(result.stdout)
    assert result["id"] == status["id"]
    assert result["favourited"] is True

    result = run(cli.statuses.unfavourite, status["id"], "--json")
    assert_ok(result)

    result = json.loads(result.stdout)
    assert result["id"] == status["id"]
    assert result["favourited"] is False


def test_reblog(app, user, run):
    status = api.post_status(app, user, "foo").json()
    assert not status["reblogged"]

    result = run(cli.statuses.reblogged_by, status["id"])
    assert_ok(result)
    assert result.stdout.strip() == "This status is not reblogged by anyone"

    result = run(cli.statuses.reblog, status["id"])
    assert_ok(result)
    assert result.stdout.strip() == "✓ Status reblogged"

    status = api.fetch_status(app, user, status["id"]).json()
    assert status["reblogged"]

    result = run(cli.statuses.reblogged_by, status["id"])
    assert_ok(result)
    assert user.username in result.stdout

    result = run(cli.statuses.unreblog, status["id"])
    assert_ok(result)
    assert result.stdout.strip() == "✓ Status unreblogged"

    status = api.fetch_status(app, user, status["id"]).json()
    assert not status["reblogged"]


def test_reblog_json(app, user, run):
    status = api.post_status(app, user, "foo").json()
    assert not status["reblogged"]

    result = run(cli.statuses.reblog, status["id"], "--json")
    assert_ok(result)

    result = json.loads(result.stdout)
    assert result["reblogged"] is True
    assert result["reblog"]["id"] == status["id"]

    result = run(cli.statuses.reblogged_by, status["id"], "--json")
    assert_ok(result)

    [reblog] = json.loads(result.stdout)
    assert reblog["acct"] == user.username

    result = run(cli.statuses.unreblog, status["id"], "--json")
    assert_ok(result)

    result = json.loads(result.stdout)
    assert result["reblogged"] is False
    assert result["reblog"] is None


def test_pin(app, user, run):
    status = api.post_status(app, user, "foo").json()
    assert not status["pinned"]

    result = run(cli.statuses.pin, status["id"])
    assert_ok(result)
    assert result.stdout.strip() == "✓ Status pinned"

    status = api.fetch_status(app, user, status["id"]).json()
    assert status["pinned"]

    result = run(cli.statuses.unpin, status["id"])
    assert_ok(result)
    assert result.stdout.strip() == "✓ Status unpinned"

    status = api.fetch_status(app, user, status["id"]).json()
    assert not status["pinned"]


def test_pin_json(app, user, run):
    status = api.post_status(app, user, "foo").json()
    assert not status["pinned"]

    result = run(cli.statuses.pin, status["id"], "--json")
    assert_ok(result)

    result = json.loads(result.stdout)
    assert result["pinned"] is True
    assert result["id"] == status["id"]

    result = run(cli.statuses.unpin, status["id"], "--json")
    assert_ok(result)

    result = json.loads(result.stdout)
    assert result["pinned"] is False
    assert result["id"] == status["id"]


def test_bookmark(app, user, run):
    status = api.post_status(app, user, "foo").json()
    assert not status["bookmarked"]

    result = run(cli.statuses.bookmark, status["id"])
    assert_ok(result)
    assert result.stdout.strip() == "✓ Status bookmarked"

    status = api.fetch_status(app, user, status["id"]).json()
    assert status["bookmarked"]

    result = run(cli.statuses.unbookmark, status["id"])
    assert_ok(result)
    assert result.stdout.strip() == "✓ Status unbookmarked"

    status = api.fetch_status(app, user, status["id"]).json()
    assert not status["bookmarked"]


def test_bookmark_json(app, user, run):
    status = api.post_status(app, user, "foo").json()
    assert not status["bookmarked"]

    result = run(cli.statuses.bookmark, status["id"], "--json")
    assert_ok(result)

    result = json.loads(result.stdout)
    assert result["id"] == status["id"]
    assert result["bookmarked"] is True

    result = run(cli.statuses.unbookmark, status["id"], "--json")
    assert_ok(result)

    result = json.loads(result.stdout)
    assert result["id"] == status["id"]
    assert result["bookmarked"] is False
