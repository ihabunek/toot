import json
import re

from tests.integration.conftest import TOOT_TEST_BASE_URL, assert_ok
from toot import api, cli
from toot.entities import Account, Status, from_dict, from_dict_list
from uuid import uuid4


def test_instance_default(app, run):
    result = run(cli.read.instance)
    assert_ok(result)

    assert "Mastodon" in result.stdout
    assert app.instance in result.stdout
    assert "running Mastodon" in result.stdout


def test_instance_with_url(app, run):
    result = run(cli.read.instance, TOOT_TEST_BASE_URL)
    assert_ok(result)

    assert "Mastodon" in result.stdout
    assert app.instance in result.stdout
    assert "running Mastodon" in result.stdout


def test_instance_json(app, run):
    result = run(cli.read.instance, "--json")
    assert_ok(result)

    data = json.loads(result.stdout)
    assert data["title"] is not None
    assert data["description"] is not None
    assert data["version"] is not None


def test_instance_anon(app, run_anon, base_url):
    result = run_anon(cli.read.instance, base_url)
    assert_ok(result)

    assert "Mastodon" in result.stdout
    assert app.instance in result.stdout
    assert "running Mastodon" in result.stdout

    # Need to specify the instance name when running anon
    result = run_anon(cli.read.instance)
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: INSTANCE argument not given and not logged in"


def test_whoami(user, run):
    result = run(cli.read.whoami)
    assert_ok(result)
    assert f"@{user.username}" in result.stdout


def test_whoami_json(user, run):
    result = run(cli.read.whoami, "--json")
    assert_ok(result)

    data = json.loads(result.stdout)
    account = from_dict(Account, data)
    assert account.username == user.username
    assert account.acct == user.username


def test_whois(app, friend, run):
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


def test_whois_json(app, friend, run):
    result = run(cli.read.whois, friend.username, "--json")
    assert_ok(result)

    data = json.loads(result.stdout)
    account = from_dict(Account, data)
    assert account.username == friend.username
    assert account.acct == friend.username


def test_search_account(friend, run):
    result = run(cli.read.search, friend.username)
    assert_ok(result)
    assert result.stdout.strip() == f"Accounts:\n* @{friend.username}"


def test_search_account_json(friend, run):
    result = run(cli.read.search, friend.username, "--json")
    assert_ok(result)

    data = json.loads(result.stdout)
    [account] = from_dict_list(Account, data["accounts"])
    assert account.acct == friend.username


def test_search_hashtag(app, user, run):
    api.post_status(app, user, "#hashtag_x")
    api.post_status(app, user, "#hashtag_y")
    api.post_status(app, user, "#hashtag_z")

    result = run(cli.read.search, "#hashtag")
    assert_ok(result)
    assert result.stdout.strip() == "Hashtags:\n#hashtag_x, #hashtag_y, #hashtag_z"


def test_search_hashtag_json(app, user, run):
    api.post_status(app, user, "#hashtag_x")
    api.post_status(app, user, "#hashtag_y")
    api.post_status(app, user, "#hashtag_z")

    result = run(cli.read.search, "#hashtag", "--json")
    assert_ok(result)

    data = json.loads(result.stdout)
    [h1, h2, h3] = sorted(data["hashtags"], key=lambda h: h["name"])

    assert h1["name"] == "hashtag_x"
    assert h2["name"] == "hashtag_y"
    assert h3["name"] == "hashtag_z"


def test_status(app, user, run):
    uuid = str(uuid4())
    status_id = api.post_status(app, user, uuid).json()["id"]

    result = run(cli.read.status, status_id)
    assert_ok(result)

    out = result.stdout.strip()
    assert uuid in out
    assert user.username in out
    assert status_id in out


def test_status_json(app, user, run):
    uuid = str(uuid4())
    status_id = api.post_status(app, user, uuid).json()["id"]

    result = run(cli.read.status, status_id, "--json")
    assert_ok(result)

    status = from_dict(Status, json.loads(result.stdout))
    assert status.id == status_id
    assert status.account.acct == user.username
    assert uuid in status.content


def test_thread(app, user, run):
    uuid1 = str(uuid4())
    uuid2 = str(uuid4())
    uuid3 = str(uuid4())

    s1 = api.post_status(app, user, uuid1).json()
    s2 = api.post_status(app, user, uuid2, in_reply_to_id=s1["id"]).json()
    s3 = api.post_status(app, user, uuid3, in_reply_to_id=s2["id"]).json()

    for status in [s1, s2, s3]:
        result = run(cli.read.thread, status["id"])
        assert_ok(result)

        bits = re.split(r"─+", result.stdout.strip())
        bits = [b for b in bits if b]

        assert len(bits) == 3

        assert s1["id"] in bits[0]
        assert s2["id"] in bits[1]
        assert s3["id"] in bits[2]

        assert uuid1 in bits[0]
        assert uuid2 in bits[1]
        assert uuid3 in bits[2]


def test_thread_json(app, user, run):
    uuid1 = str(uuid4())
    uuid2 = str(uuid4())
    uuid3 = str(uuid4())

    s1 = api.post_status(app, user, uuid1).json()
    s2 = api.post_status(app, user, uuid2, in_reply_to_id=s1["id"]).json()
    s3 = api.post_status(app, user, uuid3, in_reply_to_id=s2["id"]).json()

    result = run(cli.read.thread, s2["id"], "--json")
    assert_ok(result)

    result = json.loads(result.stdout)
    [ancestor] = [from_dict(Status, s) for s in result["ancestors"]]
    [descendent] = [from_dict(Status, s) for s in result["descendants"]]

    assert ancestor.id == s1["id"]
    assert descendent.id == s3["id"]
