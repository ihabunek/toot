from toot import cli
from toot.entities import Tag, from_dict, from_dict_list


def test_tags(run, base_url):
    result = run(cli.tags)
    assert result.exit_code == 0
    assert result.stdout.strip() == "You're not following any hashtags."

    result = run(cli.tags, "follow", "foo")
    assert result.exit_code == 0
    assert result.stdout.strip() == "✓ You are now following #foo"

    result = run(cli.tags)
    assert result.exit_code == 0
    assert result.stdout.strip() == f"* #foo\t{base_url}/tags/foo"

    result = run(cli.tags, "follow", "bar")
    assert result.exit_code == 0
    assert result.stdout.strip() == "✓ You are now following #bar"

    result = run(cli.tags)
    assert result.exit_code == 0
    assert result.stdout.strip() == "\n".join([
        f"* #bar\t{base_url}/tags/bar",
        f"* #foo\t{base_url}/tags/foo",
    ])

    result = run(cli.tags, "unfollow", "foo")
    assert result.exit_code == 0
    assert result.stdout.strip() == "✓ You are no longer following #foo"

    result = run(cli.tags)
    assert result.exit_code == 0
    assert result.stdout.strip() == f"* #bar\t{base_url}/tags/bar"

    result = run(cli.tags, "unfollow", "bar")
    assert result.exit_code == 0
    assert result.stdout.strip() == "✓ You are no longer following #bar"

    result = run(cli.tags)
    assert result.exit_code == 0
    assert result.stdout.strip() == "You're not following any hashtags."


def test_tags_json(run_json):
    result = run_json(cli.tags, "--json")
    assert result == []

    result = run_json(cli.tags, "follow", "foo", "--json")
    tag = from_dict(Tag, result)
    assert tag.name == "foo"
    assert tag.following is True

    result = run_json(cli.tags, "--json")
    [tag] = from_dict_list(Tag, result)
    assert tag.name == "foo"
    assert tag.following is True

    result = run_json(cli.tags, "follow", "bar", "--json")
    tag = from_dict(Tag, result)
    assert tag.name == "bar"
    assert tag.following is True

    result = run_json(cli.tags, "--json")
    tags = from_dict_list(Tag, result)
    [bar, foo] = sorted(tags, key=lambda t: t.name)
    assert foo.name == "foo"
    assert foo.following is True
    assert bar.name == "bar"
    assert bar.following is True

    result = run_json(cli.tags, "unfollow", "foo", "--json")
    tag = from_dict(Tag, result)
    assert tag.name == "foo"
    assert tag.following is False

    result = run_json(cli.tags, "unfollow", "bar", "--json")
    tag = from_dict(Tag, result)
    assert tag.name == "bar"
    assert tag.following is False

    result = run_json(cli.tags, "--json")
    assert result == []
