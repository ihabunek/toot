import json
from tests.integration.conftest import Run, assert_error, assert_ok, posted_status_id, strip_ansi
from toot import App, User, api, cli


def test_show_poll(app: App, user: User, run: Run):
    result = run(
        cli.post.post, "Answer me this",
        "--poll-option", "foo",
        "--poll-option", "bar",
        "--poll-option", "baz",
    )
    assert_ok(result)

    status_id = posted_status_id(result.stdout)
    status = api.fetch_status(app, user, status_id).json()
    poll_id = status["poll"]["id"]

    result = run(cli.polls.show, poll_id)
    assert_ok(result)

    assert "foo" in result.stdout
    assert "bar" in result.stdout
    assert "baz" in result.stdout
    assert f"Poll {poll_id}" in result.stdout


def test_show_poll_json(app: App, user: User, run: Run):
    result = run(
        cli.post.post, "Answer me this",
        "--poll-option", "foo",
        "--poll-option", "bar",
        "--poll-option", "baz",
    )
    assert_ok(result)

    status_id = posted_status_id(result.stdout)
    status = api.fetch_status(app, user, status_id).json()
    poll_id = status["poll"]["id"]

    result = run(cli.polls.show, poll_id, "--json")
    assert_ok(result)

    poll = json.loads(result.stdout)
    assert poll["id"] == poll_id
    assert poll["options"] == [
        {"title": "foo", "votes_count": 0},
        {"title": "bar", "votes_count": 0},
        {"title": "baz", "votes_count": 0},
    ]
    assert poll["multiple"] is False


def test_vote_poll(app: App, user: User, friend: User, run: Run, run_as: Run):
    result = run(
        cli.post.post, 
        "Answer me this",
        "--poll-option", "foo",
        "--poll-option", "bar",
        "--poll-option", "baz",
    )
    assert_ok(result)

    status_id = posted_status_id(result.stdout)
    status = api.fetch_status(app, user, status_id).json()
    poll_id = status["poll"]["id"]

    result = run_as(friend, cli.polls.vote, poll_id, "0")
    assert_ok(result)

    output_lines = strip_ansi(result.stdout).split("\n")
    assert "foo  ✓ Your vote" in output_lines
    assert "bar" in output_lines
    assert "baz" in output_lines

    # Voting a second time should not succeed
    result = run_as(friend, cli.polls.vote, poll_id, "0")
    assert_error(result, "You have already voted on this poll")


def test_vote_poll_invalid_choice(app: App, user: User, friend: User, run: Run, run_as: Run):
    result = run(
        cli.post.post,
        "Answer me this",
        "--poll-option", "foo",
        "--poll-option", "bar",
        "--poll-option", "baz",
    )
    assert_ok(result)

    status_id = posted_status_id(result.stdout)
    status = api.fetch_status(app, user, status_id).json()
    poll_id = status["poll"]["id"]

    result = run_as(friend, cli.polls.vote, poll_id, "5")  # invalid index
    assert_error(result, "The chosen vote option does not exist")


def test_vote_not_multiple(app: App, user: User, friend: User, run: Run, run_as: Run):
    result = run(
        cli.post.post,
        "Answer me this",
        "--poll-option", "foo",
        "--poll-option", "bar",
        "--poll-option", "baz",
    )
    assert_ok(result)

    status_id = posted_status_id(result.stdout)
    status = api.fetch_status(app, user, status_id).json()
    poll_id = status["poll"]["id"]

    # Voting on multiple choices when poll is not multiple
    result = run_as(friend, cli.polls.vote, poll_id, "0", "2")
    # NB: Mastodon returns the wrong error here
    assert_error(result, "You have already voted on this poll")


def test_vote_poll_multiple(app: App, user: User, friend: User, run: Run, run_as: Run):
    result = run(
        cli.post.post,
        "Answer me this",
        "--poll-option", "foo",
        "--poll-option", "bar",
        "--poll-option", "baz",
        "--poll-multiple"
    )
    assert_ok(result)

    status_id = posted_status_id(result.stdout)
    status = api.fetch_status(app, user, status_id).json()
    poll_id = status["poll"]["id"]

    result = run_as(friend, cli.polls.vote, poll_id, "0", "2")
    assert_ok(result)

    output_lines = strip_ansi(result.stdout).split("\n")
    assert "foo  ✓ Your vote" in output_lines
    assert "bar" in output_lines
    assert "baz  ✓ Your vote" in output_lines

    # Voting a second time should not succeed
    result = run_as(friend, cli.polls.vote, poll_id, "0", "2")
    assert_error(result, "You have already voted on this poll")
