import re
from typing import List

from tests.integration.conftest import assert_ok
from toot import api, cli
from toot.entities import FeaturedTag, Tag, from_dict, from_dict_list


def test_tags(run):
    result = run(cli.tags.tags, "followed")
    assert_ok(result)
    assert result.stdout.strip() == "You're not following any hashtags"

    result = run(cli.tags.tags, "follow", "foo")
    assert_ok(result)
    assert result.stdout.strip() == "✓ You are now following #foo"

    result = run(cli.tags.tags, "followed")
    assert_ok(result)
    assert _find_tags(result.stdout) == ["#foo"]

    result = run(cli.tags.tags, "follow", "bar")
    assert_ok(result)
    assert result.stdout.strip() == "✓ You are now following #bar"

    result = run(cli.tags.tags, "followed")
    assert_ok(result)
    assert _find_tags(result.stdout) == ["#bar", "#foo"]

    result = run(cli.tags.tags, "unfollow", "foo")
    assert_ok(result)
    assert result.stdout.strip() == "✓ You are no longer following #foo"

    result = run(cli.tags.tags, "followed")
    assert_ok(result)
    assert _find_tags(result.stdout) == ["#bar"]

    result = run(cli.tags.tags, "unfollow", "bar")
    assert_ok(result)
    assert result.stdout.strip() == "✓ You are no longer following #bar"

    result = run(cli.tags.tags, "followed")
    assert_ok(result)
    assert result.stdout.strip() == "You're not following any hashtags"


def test_tags_json(run_json):
    result = run_json(cli.tags.tags, "followed", "--json")
    assert result == []

    result = run_json(cli.tags.tags, "follow", "foo", "--json")
    tag = from_dict(Tag, result)
    assert tag.name == "foo"
    assert tag.following is True

    result = run_json(cli.tags.tags, "followed", "--json")
    [tag] = from_dict_list(Tag, result)
    assert tag.name == "foo"
    assert tag.following is True

    result = run_json(cli.tags.tags, "follow", "bar", "--json")
    tag = from_dict(Tag, result)
    assert tag.name == "bar"
    assert tag.following is True

    result = run_json(cli.tags.tags, "followed", "--json")
    tags = from_dict_list(Tag, result)
    [bar, foo] = sorted(tags, key=lambda t: t.name)
    assert foo.name == "foo"
    assert foo.following is True
    assert bar.name == "bar"
    assert bar.following is True

    result = run_json(cli.tags.tags, "unfollow", "foo", "--json")
    tag = from_dict(Tag, result)
    assert tag.name == "foo"
    assert tag.following is False

    result = run_json(cli.tags.tags, "unfollow", "bar", "--json")
    tag = from_dict(Tag, result)
    assert tag.name == "bar"
    assert tag.following is False

    result = run_json(cli.tags.tags, "followed", "--json")
    assert result == []


def test_tags_featured(run, app, user):
    result = run(cli.tags.tags, "featured")
    assert_ok(result)
    assert result.stdout.strip() == "You don't have any featured hashtags"

    result = run(cli.tags.tags, "feature", "foo")
    assert_ok(result)
    assert result.stdout.strip() == "✓ Tag #foo is now featured"

    result = run(cli.tags.tags, "featured")
    assert_ok(result)
    assert _find_tags(result.stdout) == ["#foo"]

    result = run(cli.tags.tags, "feature", "bar")
    assert_ok(result)
    assert result.stdout.strip() == "✓ Tag #bar is now featured"

    result = run(cli.tags.tags, "featured")
    assert_ok(result)
    assert _find_tags(result.stdout) == ["#bar", "#foo"]

    # Unfeature by Name
    result = run(cli.tags.tags, "unfeature", "foo")
    assert_ok(result)
    assert result.stdout.strip() == "✓ Tag #foo is no longer featured"

    result = run(cli.tags.tags, "featured")
    assert_ok(result)
    assert _find_tags(result.stdout) == ["#bar"]

    # Unfeature by ID
    tag = api.find_featured_tag(app, user, "bar")
    assert tag is not None

    result = run(cli.tags.tags, "unfeature", tag["id"])
    assert_ok(result)
    assert result.stdout.strip() == "✓ Tag #bar is no longer featured"

    result = run(cli.tags.tags, "featured")
    assert_ok(result)
    assert result.stdout.strip() == "You don't have any featured hashtags"


def test_tags_featured_json(run_json):
    result = run_json(cli.tags.tags, "featured", "--json")
    assert result == []

    result = run_json(cli.tags.tags, "feature", "foo", "--json")
    tag = from_dict(FeaturedTag, result)
    assert tag.name == "foo"

    result = run_json(cli.tags.tags, "featured", "--json")
    [tag] = from_dict_list(FeaturedTag, result)
    assert tag.name == "foo"

    result = run_json(cli.tags.tags, "feature", "bar", "--json")
    tag = from_dict(FeaturedTag, result)
    assert tag.name == "bar"

    result = run_json(cli.tags.tags, "featured", "--json")
    tags = from_dict_list(FeaturedTag, result)
    [bar, foo] = sorted(tags, key=lambda t: t.name)
    assert foo.name == "foo"
    assert bar.name == "bar"

    result = run_json(cli.tags.tags, "unfeature", "foo", "--json")
    assert result == {}

    result = run_json(cli.tags.tags, "unfeature", "bar", "--json")
    assert result == {}

    result = run_json(cli.tags.tags, "featured", "--json")
    assert result == []


def _find_tags(txt: str) -> List[str]:
    return sorted(re.findall(r"#\w+", txt))
