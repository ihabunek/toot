import json
import re
import uuid

from datetime import datetime, timedelta, timezone
from os import path
from tests.integration.conftest import ASSETS_DIR, posted_status_id
from toot import CLIENT_NAME, CLIENT_WEBSITE, api
from toot.utils import get_text
from unittest import mock


def test_post(app, user, run):
    text = "i wish i was a #lumberjack"
    out = run("post", text)
    status_id = posted_status_id(out)

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


def test_post_json(run):
    content = "i wish i was a #lumberjack"
    out = run("post", content, "--json")
    status = json.loads(out)

    assert get_text(status["content"]) == content
    assert status["visibility"] == "public"
    assert status["sensitive"] is False
    assert status["spoiler_text"] == ""
    assert status["poll"] is None


def test_post_visibility(app, user, run):
    for visibility in ["public", "unlisted", "private", "direct"]:
        out = run("post", "foo", "--visibility", visibility)
        status_id = posted_status_id(out)
        status = api.fetch_status(app, user, status_id).json()
        assert status["visibility"] == visibility


def test_post_scheduled_at(app, user, run):
    text = str(uuid.uuid4())
    scheduled_at = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=10)

    out = run("post", text, "--scheduled-at", scheduled_at.isoformat())
    assert "Toot scheduled for" in out

    statuses = api.scheduled_statuses(app, user)
    [status] = [s for s in statuses if s["params"]["text"] == text]
    assert datetime.strptime(status["scheduled_at"], "%Y-%m-%dT%H:%M:%S.%f%z") == scheduled_at


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
        out = run("post", text, "--scheduled-in", scheduled_in)
        dttm = datetime.utcnow() + delta
        assert out.startswith(f"Toot scheduled for: {str(dttm)[:16]}")
        datetimes.append(dttm)

    scheduled = api.scheduled_statuses(app, user)
    scheduled = [s for s in scheduled if s["params"]["text"] == text]
    scheduled = sorted(scheduled, key=lambda s: s["scheduled_at"])
    assert len(scheduled) == 8

    for expected, status in zip(datetimes, scheduled):
        actual = datetime.strptime(status["scheduled_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
        delta = expected - actual
        assert delta.total_seconds() < 5


def test_post_poll(app, user, run):
    text = str(uuid.uuid4())

    out = run(
        "post", text,
        "--poll-option", "foo",
        "--poll-option", "bar",
        "--poll-option", "baz",
        "--poll-option", "qux",
    )

    status_id = posted_status_id(out)

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

    out = run(
        "post", text,
        "--poll-option", "foo",
        "--poll-option", "bar",
        "--poll-multiple"
    )

    status_id = posted_status_id(out)

    status = api.fetch_status(app, user, status_id).json()
    assert status["poll"]["multiple"] is True


def test_post_poll_expires_in(app, user, run):
    text = str(uuid.uuid4())

    out = run(
        "post", text,
        "--poll-option", "foo",
        "--poll-option", "bar",
        "--poll-expires-in", "8h",
    )

    status_id = posted_status_id(out)

    status = api.fetch_status(app, user, status_id).json()
    actual = datetime.strptime(status["poll"]["expires_at"], "%Y-%m-%dT%H:%M:%S.%f%z")
    expected = datetime.now(timezone.utc) + timedelta(hours=8)
    delta = actual - expected
    assert delta.total_seconds() < 5


def test_post_poll_hide_totals(app, user, run):
    text = str(uuid.uuid4())

    out = run(
        "post", text,
        "--poll-option", "foo",
        "--poll-option", "bar",
        "--poll-hide-totals"
    )

    status_id = posted_status_id(out)

    status = api.fetch_status(app, user, status_id).json()

    # votes_count is None when totals are hidden
    assert status["poll"]["options"] == [
        {"title": "foo", "votes_count": None},
        {"title": "bar", "votes_count": None},
    ]


def test_post_language(app, user, run):
    out = run("post", "test", "--language", "hr")
    status_id = posted_status_id(out)
    status = api.fetch_status(app, user, status_id).json()
    assert status["language"] == "hr"

    out = run("post", "test", "--language", "zh")
    status_id = posted_status_id(out)
    status = api.fetch_status(app, user, status_id).json()
    assert status["language"] == "zh"


def test_media_thumbnail(app, user, run):
    video_path = path.join(ASSETS_DIR, "small.webm")
    thumbnail_path = path.join(ASSETS_DIR, "test1.png")

    out = run(
        "post",
        "--media", video_path,
        "--thumbnail", thumbnail_path,
        "--description", "foo",
        "some text"
    )

    status_id = posted_status_id(out)
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

    out = run(
        "post",
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

    status_id = posted_status_id(out)
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


@mock.patch("toot.utils.multiline_input")
@mock.patch("sys.stdin.read")
def test_media_attachment_without_text(mock_read, mock_ml, app, user, run):
    # No status from stdin or readline
    mock_read.return_value = ""
    mock_ml.return_value = ""

    media_path = path.join(ASSETS_DIR, "test1.png")

    out = run("post", "--media", media_path)
    status_id = posted_status_id(out)

    status = api.fetch_status(app, user, status_id).json()
    assert status["content"] == ""

    [attachment] = status["media_attachments"]
    assert not attachment["description"]

    # Pleroma doesn't send metadata
    if "meta" in attachment:
        assert attachment["meta"]["original"]["size"] == "50x50"


def test_reply_thread(app, user, friend, run):
    status = api.post_status(app, friend, "This is the status").json()

    out = run("post", "--reply-to", status["id"], "This is the reply")
    status_id = posted_status_id(out)
    reply = api.fetch_status(app, user, status_id).json()

    assert reply["in_reply_to_id"] == status["id"]

    out = run("thread", status["id"])
    [s1, s2] = [s.strip() for s in re.split(r"─+", out) if s.strip()]

    assert "This is the status" in s1
    assert "This is the reply" in s2
    assert friend.username in s1
    assert user.username in s2
    assert status["id"] in s1
    assert reply["id"] in s2
