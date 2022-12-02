from toot.output import colorize, strip_tags, STYLES

reset = STYLES["reset"]
red = STYLES["red"]
green = STYLES["green"]
bold = STYLES["bold"]


def test_colorize():
    assert colorize("foo") == "foo"
    assert colorize("<red>foo</red>") == f"{red}foo{reset}{reset}"
    assert colorize("foo <red>bar</red> baz") == f"foo {red}bar{reset} baz{reset}"
    assert colorize("foo <red bold>bar</red bold> baz") == f"foo {red}{bold}bar{reset} baz{reset}"
    assert colorize("foo <red bold>bar</red> baz") == f"foo {red}{bold}bar{reset}{bold} baz{reset}"
    assert colorize("foo <red bold>bar</> baz") == f"foo {red}{bold}bar{reset} baz{reset}"
    assert colorize("<red>foo<bold>bar</bold>baz</red>") == f"{red}foo{bold}bar{reset}{red}baz{reset}{reset}"


def test_strip_tags():
    assert strip_tags("foo") == "foo"
    assert strip_tags("<red>foo</red>") == "foo"
    assert strip_tags("foo <red>bar</red> baz") == "foo bar baz"
    assert strip_tags("foo <red bold>bar</red bold> baz") == "foo bar baz"
    assert strip_tags("foo <red bold>bar</red> baz") == "foo bar baz"
    assert strip_tags("foo <red bold>bar</> baz") == "foo bar baz"
    assert strip_tags("<red>foo<bold>bar</bold>baz</red>") == "foobarbaz"
