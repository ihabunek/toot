import json
import re
import uuid

from datetime import datetime, timedelta, timezone
from os import path

from tests.integration.conftest import ASSETS_DIR, Run, assert_ok, posted_status_id
from toot import CLIENT_NAME, CLIENT_WEBSITE, api, cli
from toot.cache import clear_last_post_id, get_last_post_id
from toot.utils import get_text
from unittest import mock


def test_post(app, user, run: Run):
    text = "i wish i was a #lumberjack"
    result = run(cli.post.post, text)
    assert_ok(result)

    status_id = posted_status_id(result.stdout)

    status = api.fetch_status(app, user, status_id).json()
    assert text == get_text(status["content"])
    assert status["visibility"] == "public"
    assert status["sensitive"] is False
    assert status["spoiler_text"] == ""
    assert status["poll"] is None

    # Pleroma doesn't return the application
    if status["application"]:
        assert status["application"]["name"] == CLIENT_NAME
        assert status["application"]["website"] == CLIENT_WEBSITE


def test_post_no_text(run):
    result = run(cli.post.post)
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: You must specify either text or media to post."


def test_post_json(run):
    content = "i wish i was a #lumberjack"
    result = run(cli.post.post, content, "--json")
    assert_ok(result)

    status = json.loads(result.stdout)
    assert get_text(status["content"]) == content
    assert status["visibility"] == "public"
    assert status["sensitive"] is False
    assert status["spoiler_text"] == ""
    assert status["poll"] is None


def test_post_visibility(app, user, run):
    for visibility in ["public", "unlisted", "private", "direct"]:
        result = run(cli.post.post, "foo", "--visibility", visibility)
        assert_ok(result)

        status_id = posted_status_id(result.stdout)
        status = api.fetch_status(app, user, status_id).json()
        assert status["visibility"] == visibility


def test_post_scheduled_at(app, user, run):
    text = str(uuid.uuid4())
    scheduled_at = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=10)

    result = run(cli.post.post, text, "--scheduled-at", scheduled_at.isoformat())
    assert_ok(result)

    assert "Toot scheduled for" in result.stdout

    statuses = api.scheduled_statuses(app, user)
    [status] = [s for s in statuses if s["params"]["text"] == text]
    assert datetime.strptime(status["scheduled_at"], "%Y-%m-%dT%H:%M:%S.%f%z") == scheduled_at


def test_post_scheduled_at_error(run):
    result = run(cli.post.post, "foo", "--scheduled-at", "banana")
    assert result.exit_code == 1
    # Stupid error returned by mastodon
    assert result.stderr.strip() == "Error: Record invalid"


def test_post_scheduled_in(app, user, run):
    text = str(uuid.uuid4())

    variants = [
        ("1 day", timedelta(days=1)),
        ("1 day 6 hours", timedelta(days=1, hours=6)),
        ("1 day 6 hours 13 minutes", timedelta(days=1, hours=6, minutes=13)),
        ("1 day 6 hours 13 minutes 51 second", timedelta(days=1, hours=6, minutes=13, seconds=51)),
        ("2d", timedelta(days=2)),
        ("2d6h", timedelta(days=2, hours=6)),
        ("2d6h13m", timedelta(days=2, hours=6, minutes=13)),
        ("2d6h13m51s", timedelta(days=2, hours=6, minutes=13, seconds=51)),
    ]

    datetimes = []
    for scheduled_in, delta in variants:
        result = run(cli.post.post, text, "--scheduled-in", scheduled_in)
        assert_ok(result)

        dttm = datetime.now(timezone.utc) + delta
        assert result.stdout.startswith(f"Toot scheduled for: {str(dttm)[:16]}")
        datetimes.append(dttm)

    scheduled = api.scheduled_statuses(app, user)
    scheduled = [s for s in scheduled if s["params"]["text"] == text]
    scheduled = sorted(scheduled, key=lambda s: s["scheduled_at"])
    assert len(scheduled) == 8

    for expected, status in zip(datetimes, scheduled):
        actual = datetime.strptime(status["scheduled_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        delta = expected - actual
        assert delta.total_seconds() < 5


def test_post_scheduled_in_invalid_duration(run):
    result = run(cli.post.post, "foo", "--scheduled-in", "banana")
    assert result.exit_code == 2
    assert "Invalid duration: banana" in result.stderr


def test_post_scheduled_in_empty_duration(run):
    result = run(cli.post.post, "foo", "--scheduled-in", "0m")
    assert result.exit_code == 2
    assert "Empty duration" in result.stderr


def test_post_poll(app, user, run):
    text = str(uuid.uuid4())

    result = run(
        cli.post.post, text,
        "--poll-option", "foo",
        "--poll-option", "bar",
        "--poll-option", "baz",
        "--poll-option", "qux",
    )

    assert_ok(result)
    status_id = posted_status_id(result.stdout)

    status = api.fetch_status(app, user, status_id).json()
    assert status["poll"]["expired"] is False
    assert status["poll"]["multiple"] is False
    assert status["poll"]["options"] == [
        {"title": "foo", "votes_count": 0},
        {"title": "bar", "votes_count": 0},
        {"title": "baz", "votes_count": 0},
        {"title": "qux", "votes_count": 0}
    ]

    # Test expires_at is 24h by default
    actual = datetime.strptime(status["poll"]["expires_at"], "%Y-%m-%dT%H:%M:%S.%f%z")
    expected = datetime.now(timezone.utc) + timedelta(days=1)
    delta = actual - expected
    assert delta.total_seconds() < 5


def test_post_poll_multiple(app, user, run):
    text = str(uuid.uuid4())

    result = run(
        cli.post.post, text,
        "--poll-option", "foo",
        "--poll-option", "bar",
        "--poll-multiple"
    )
    assert_ok(result)

    status_id = posted_status_id(result.stdout)
    status = api.fetch_status(app, user, status_id).json()
    assert status["poll"]["multiple"] is True


def test_post_poll_expires_in(app, user, run):
    text = str(uuid.uuid4())

    result = run(
        cli.post.post, text,
        "--poll-option", "foo",
        "--poll-option", "bar",
        "--poll-expires-in", "8h",
    )
    assert_ok(result)

    status_id = posted_status_id(result.stdout)

    status = api.fetch_status(app, user, status_id).json()
    actual = datetime.strptime(status["poll"]["expires_at"], "%Y-%m-%dT%H:%M:%S.%f%z")
    expected = datetime.now(timezone.utc) + timedelta(hours=8)
    delta = actual - expected
    assert delta.total_seconds() < 5


def test_post_poll_hide_totals(app, user, run):
    text = str(uuid.uuid4())

    result = run(
        cli.post.post, text,
        "--poll-option", "foo",
        "--poll-option", "bar",
        "--poll-hide-totals"
    )
    assert_ok(result)

    status_id = posted_status_id(result.stdout)

    status = api.fetch_status(app, user, status_id).json()

    # votes_count is None when totals are hidden
    assert status["poll"]["options"] == [
        {"title": "foo", "votes_count": None},
        {"title": "bar", "votes_count": None},
    ]


def test_post_language(app, user, run):
    result = run(cli.post.post, "test", "--language", "hr")
    assert_ok(result)

    status_id = posted_status_id(result.stdout)
    status = api.fetch_status(app, user, status_id).json()
    assert status["language"] == "hr"

    result = run(cli.post.post, "test", "--language", "zh")
    assert_ok(result)

    status_id = posted_status_id(result.stdout)
    status = api.fetch_status(app, user, status_id).json()
    assert status["language"] == "zh"


def test_post_language_error(run):
    result = run(cli.post.post, "test", "--language", "banana")
    assert result.exit_code == 2
    assert "Language should be a two letter abbreviation." in result.stderr


def test_media_thumbnail(app, user, run):
    video_path = path.join(ASSETS_DIR, "small.webm")
    thumbnail_path = path.join(ASSETS_DIR, "test1.png")

    result = run(
        cli.post.post,
        "--media", video_path,
        "--thumbnail", thumbnail_path,
        "--description", "foo",
        "some text"
    )
    assert_ok(result)

    status_id = posted_status_id(result.stdout)
    status = api.fetch_status(app, user, status_id).json()
    [media] = status["media_attachments"]

    assert media["description"] == "foo"
    assert media["type"] == "video"
    assert media["url"].endswith(".mp4")
    assert media["preview_url"].endswith(".png")

    # Video properties
    assert int(media["meta"]["original"]["duration"]) == 5
    assert media["meta"]["original"]["height"] == 320
    assert media["meta"]["original"]["width"] == 560

    # Thumbnail properties
    assert media["meta"]["small"]["height"] == 50
    assert media["meta"]["small"]["width"] == 50


def test_media_attachments(app, user, run):
    path1 = path.join(ASSETS_DIR, "test1.png")
    path2 = path.join(ASSETS_DIR, "test2.png")
    path3 = path.join(ASSETS_DIR, "test3.png")
    path4 = path.join(ASSETS_DIR, "test4.png")

    result = run(
        cli.post.post,
        "--media", path1,
        "--media", path2,
        "--media", path3,
        "--media", path4,
        "--description", "Test 1",
        "--description", "Test 2",
        "--description", "Test 3",
        "--description", "Test 4",
        "some text"
    )
    assert_ok(result)

    status_id = posted_status_id(result.stdout)
    status = api.fetch_status(app, user, status_id).json()

    [a1, a2, a3, a4] = status["media_attachments"]

    # Pleroma doesn't send metadata
    if "meta" in a1:
        assert a1["meta"]["original"]["size"] == "50x50"
        assert a2["meta"]["original"]["size"] == "50x60"
        assert a3["meta"]["original"]["size"] == "50x70"
        assert a4["meta"]["original"]["size"] == "50x80"

    assert a1["description"] == "Test 1"
    assert a2["description"] == "Test 2"
    assert a3["description"] == "Test 3"
    assert a4["description"] == "Test 4"


def test_too_many_media(run):
    m = path.join(ASSETS_DIR, "test1.png")
    result = run(cli.post.post, "-m", m, "-m", m, "-m", m, "-m", m, "-m", m)
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: Cannot attach more than 4 files."


@mock.patch("toot.utils.multiline_input")
@mock.patch("sys.stdin.read")
def test_media_attachment_without_text(mock_read, mock_ml, app, user, run):
    # No status from stdin or readline
    mock_read.return_value = ""
    mock_ml.return_value = ""

    media_path = path.join(ASSETS_DIR, "test1.png")

    result = run(cli.post.post, "--media", media_path)
    assert_ok(result)

    status_id = posted_status_id(result.stdout)

    status = api.fetch_status(app, user, status_id).json()
    assert status["content"] == ""

    [attachment] = status["media_attachments"]
    assert not attachment["description"]

    # Pleroma doesn't send metadata
    if "meta" in attachment:
        assert attachment["meta"]["original"]["size"] == "50x50"


def test_reply_to(app, user, friend, run):
    status = api.post_status(app, friend, "This is the status").json()

    result = run(cli.post.post, "--reply-to", status["id"], "This is the reply")
    assert_ok(result)

    status_id = posted_status_id(result.stdout)
    reply = api.fetch_status(app, user, status_id).json()

    assert reply["in_reply_to_id"] == status["id"]

    result = run(cli.read.thread, status["id"])
    assert_ok(result)

    [s1, s2] = [s.strip() for s in re.split(r"─+", result.stdout) if s.strip()]

    assert "This is the status" in s1
    assert "This is the reply" in s2
    assert friend.username in s1
    assert user.username in s2
    assert status["id"] in s1
    assert reply["id"] in s2


def test_reply_last(app, user, run):
    result_1 = run(cli.post.post, "one")
    status_id_1 = posted_status_id(result_1.stdout)
    assert get_last_post_id(app, user) == status_id_1

    result_2 = run(cli.post.post, "two", "--reply-last")
    status_id_2 = posted_status_id(result_2.stdout)
    assert get_last_post_id(app, user) == status_id_2

    result_3 = run(cli.post.post, "two", "--reply-last")
    status_id_3 = posted_status_id(result_3.stdout)
    assert get_last_post_id(app, user) == status_id_3

    status_1 = api.fetch_status(app, user, status_id_1).json()
    status_2 = api.fetch_status(app, user, status_id_2).json()
    status_3 = api.fetch_status(app, user, status_id_3).json()

    assert status_1["in_reply_to_id"] is None
    assert status_2["in_reply_to_id"] == status_id_1
    assert status_3["in_reply_to_id"] == status_id_2


def test_reply_last_fails_if_no_last_id(app, user, run: Run):
    clear_last_post_id(app, user)
    result = run(cli.post.post, "one", "--reply-last")
    assert result.exit_code == 1
    assert result.stderr.strip() == f"Error: Cannot reply-last, no previous post ID found for {user.username}@{app.instance}"


def test_reply_last_and_reply_to_are_exclusive(app, user, run: Run):
    result = run(cli.post.post, "one", "--reply-last", "--reply-to", "123")
    assert result.exit_code == 1
    assert result.stderr.strip() == f"Error: --reply-last and --reply-to are mutually exclusive"
