from datetime import datetime
import click
import pytest
import sys

from toot.cli.validators import validate_duration
from toot.utils.datetime import parse_datetime
from toot.wcstring import wc_wrap, trunc, pad, fit_text
from toot.tui.utils import LRUCache
from PIL import Image
from collections import namedtuple
from toot.utils import batched, urlencode_url


def test_pad():
    # guitar symbol will occupy two cells, so padded text should be 1
    # character shorter
    text = 'Frank Zappa 🎸'

    # Negative values are basically ignored
    assert pad(text, -100) is text

    # Padding to length smaller than text length does nothing
    assert pad(text, 11) is text
    assert pad(text, 12) is text
    assert pad(text, 13) is text
    assert pad(text, 14) is text

    assert pad(text, 15) == 'Frank Zappa 🎸 '
    assert pad(text, 16) == 'Frank Zappa 🎸  '
    assert pad(text, 17) == 'Frank Zappa 🎸   '
    assert pad(text, 18) == 'Frank Zappa 🎸    '
    assert pad(text, 19) == 'Frank Zappa 🎸     '
    assert pad(text, 20) == 'Frank Zappa 🎸      '


def test_trunc():
    text = 'Frank Zappa 🎸'

    assert trunc(text, 1)  == '…'
    assert trunc(text, 2)  == 'F…'
    assert trunc(text, 3)  == 'Fr…'
    assert trunc(text, 4)  == 'Fra…'
    assert trunc(text, 5)  == 'Fran…'
    assert trunc(text, 6)  == 'Frank…'
    assert trunc(text, 7)  == 'Frank…'
    assert trunc(text, 8)  == 'Frank Z…'
    assert trunc(text, 9)  == 'Frank Za…'
    assert trunc(text, 10) == 'Frank Zap…'
    assert trunc(text, 11) == 'Frank Zapp…'
    assert trunc(text, 12) == 'Frank Zappa…'
    assert trunc(text, 13) == 'Frank Zappa…'

    # Truncating to length larger than text length does nothing
    assert trunc(text, 14) is text
    assert trunc(text, 15) is text
    assert trunc(text, 16) is text
    assert trunc(text, 17) is text
    assert trunc(text, 18) is text
    assert trunc(text, 19) is text
    assert trunc(text, 20) is text


def test_fit_text():
    text = 'Frank Zappa 🎸'

    assert fit_text(text, 1)  == '…'
    assert fit_text(text, 2)  == 'F…'
    assert fit_text(text, 3)  == 'Fr…'
    assert fit_text(text, 4)  == 'Fra…'
    assert fit_text(text, 5)  == 'Fran…'
    assert fit_text(text, 6)  == 'Frank…'
    assert fit_text(text, 7)  == 'Frank…'
    assert fit_text(text, 8)  == 'Frank Z…'
    assert fit_text(text, 9)  == 'Frank Za…'
    assert fit_text(text, 10) == 'Frank Zap…'
    assert fit_text(text, 11) == 'Frank Zapp…'
    assert fit_text(text, 12) == 'Frank Zappa…'
    assert fit_text(text, 13) == 'Frank Zappa…'
    assert fit_text(text, 14) == 'Frank Zappa 🎸'
    assert fit_text(text, 15) == 'Frank Zappa 🎸 '
    assert fit_text(text, 16) == 'Frank Zappa 🎸  '
    assert fit_text(text, 17) == 'Frank Zappa 🎸   '
    assert fit_text(text, 18) == 'Frank Zappa 🎸    '
    assert fit_text(text, 19) == 'Frank Zappa 🎸     '
    assert fit_text(text, 20) == 'Frank Zappa 🎸      '


def test_wc_wrap_plain_text():
    lorem = (
        "Eius voluptas eos praesentium et tempore. Quaerat nihil voluptatem "
        "excepturi reiciendis sapiente voluptate natus. Tenetur occaecati "
        "velit dicta dolores. Illo reiciendis nulla ea. Facilis nostrum non "
        "qui inventore sit."
    )

    assert list(wc_wrap(lorem, 50)) == [
        #01234567890123456789012345678901234567890123456789 # noqa
        "Eius voluptas eos praesentium et tempore. Quaerat",
        "nihil voluptatem excepturi reiciendis sapiente",
        "voluptate natus. Tenetur occaecati velit dicta",
        "dolores. Illo reiciendis nulla ea. Facilis nostrum",
        "non qui inventore sit.",
    ]


def test_wc_wrap_plain_text_wrap_on_any_whitespace():
    lorem = (
        "Eius\t\tvoluptas\teos\tpraesentium\tet\ttempore.\tQuaerat\tnihil\tvoluptatem\t"
        "excepturi\nreiciendis\n\nsapiente\nvoluptate\nnatus.\nTenetur\noccaecati\n"
        "velit\rdicta\rdolores.\rIllo\rreiciendis\rnulla\r\r\rea.\rFacilis\rnostrum\rnon\r"
        "qui\u2003inventore\u2003\u2003sit."  # em space
    )

    assert list(wc_wrap(lorem, 50)) == [
        #01234567890123456789012345678901234567890123456789 # noqa
        "Eius voluptas eos praesentium et tempore. Quaerat",
        "nihil voluptatem excepturi reiciendis sapiente",
        "voluptate natus. Tenetur occaecati velit dicta",
        "dolores. Illo reiciendis nulla ea. Facilis nostrum",
        "non qui inventore sit.",
    ]


def test_wc_wrap_text_with_wide_chars():
    lorem = (
        "☕☕☕☕☕ voluptas eos praesentium et 🎸🎸🎸🎸🎸. Quaerat nihil "
        "voluptatem excepturi reiciendis sapiente voluptate natus."
    )

    assert list(wc_wrap(lorem, 50)) == [
        #01234567890123456789012345678901234567890123456789 # noqa
        "☕☕☕☕☕ voluptas eos praesentium et 🎸🎸🎸🎸🎸.",
        "Quaerat nihil voluptatem excepturi reiciendis",
        "sapiente voluptate natus.",
    ]


def test_wc_wrap_hard_wrap():
    lorem = (
        "☕☕☕☕☕voluptaseospraesentiumet🎸🎸🎸🎸🎸.Quaeratnihil"
        "voluptatemexcepturireiciendissapientevoluptatenatus."
    )

    assert list(wc_wrap(lorem, 50)) == [
        #01234567890123456789012345678901234567890123456789 # noqa
        "☕☕☕☕☕voluptaseospraesentiumet🎸🎸🎸🎸🎸.Quaer",
        "atnihilvoluptatemexcepturireiciendissapientevolupt",
        "atenatus.",
    ]


def test_wc_wrap_indented():
    lorem = (
        "     Eius voluptas eos praesentium et tempore. Quaerat nihil voluptatem "
        "     excepturi reiciendis sapiente voluptate natus. Tenetur occaecati "
        "     velit dicta dolores. Illo reiciendis nulla ea. Facilis nostrum non "
        "     qui inventore sit."
    )

    assert list(wc_wrap(lorem, 50)) == [
        #01234567890123456789012345678901234567890123456789 # noqa
        "Eius voluptas eos praesentium et tempore. Quaerat",
        "nihil voluptatem excepturi reiciendis sapiente",
        "voluptate natus. Tenetur occaecati velit dicta",
        "dolores. Illo reiciendis nulla ea. Facilis nostrum",
        "non qui inventore sit.",
    ]


def test_duration():
    def duration(value):
        return validate_duration(None, None, value)

    # Long hand
    assert duration("1 second") == 1
    assert duration("1 seconds") == 1
    assert duration("100 second") == 100
    assert duration("100 seconds") == 100
    assert duration("5 minutes") == 5 * 60
    assert duration("5 minutes 10 seconds") == 5 * 60 + 10
    assert duration("1 hour 5 minutes") == 3600 + 5 * 60
    assert duration("1 hour 5 minutes 1 second") == 3600 + 5 * 60 + 1
    assert duration("5 days") == 5 * 86400
    assert duration("5 days 3 minutes") == 5 * 86400 + 3 * 60
    assert duration("5 days 10 hours 3 minutes 1 second") == 5 * 86400 + 10 * 3600 + 3 * 60 + 1

    # Short hand
    assert duration("1s") == 1
    assert duration("100s") == 100
    assert duration("5m") == 5 * 60
    assert duration("5m10s") == 5 * 60 + 10
    assert duration("5m 10s") == 5 * 60 + 10
    assert duration("1h5m1s") == 3600 + 5 * 60 + 1
    assert duration("1h 5m 1s") == 3600 + 5 * 60 + 1
    assert duration("5d") == 5 * 86400
    assert duration("5d3m") == 5 * 86400 + 3 * 60
    assert duration("5d 3m") == 5 * 86400 + 3 * 60
    assert duration("5d 10h 3m 1s") == 5 * 86400 + 10 * 3600 + 3 * 60 + 1
    assert duration("5d10h3m1s") == 5 * 86400 + 10 * 3600 + 3 * 60 + 1

    with pytest.raises(click.BadParameter):
        duration("")

    with pytest.raises(click.BadParameter):
        duration("100")

    # Wrong order
    with pytest.raises(click.BadParameter):
        duration("1m1d")

    with pytest.raises(click.BadParameter):
        duration("banana")


def test_cache_null():
    """Null dict is null."""
    cache = LRUCache(cache_max_bytes=1024)
    assert cache.__len__() == 0


Case = namedtuple("Case", ["cache_len", "len", "init"])

img = Image.new('RGB', (100, 100))
img_size = sys.getsizeof(img.tobytes())

@pytest.mark.parametrize(
    "case",
    [
        Case(9, 0, []),
        Case(9, 1, [("one", img)]),
        Case(9, 2, [("one", img), ("two", img)]),
        Case(2, 2, [("one", img), ("two", img)]),
        Case(1, 1, [("one", img), ("two", img)]),
    ],
)
@pytest.mark.parametrize("method", ["assign", "init"])
def test_cache_init(case, method):
    """Check that the # of elements is right, given # given and cache_len."""
    if method == "init":
        cache = LRUCache(case.init, cache_max_bytes=img_size * case.cache_len)
    elif method == "assign":
        cache = LRUCache(cache_max_bytes=img_size * case.cache_len)
        for (key, val) in case.init:
            cache[key] = val
    else:
        assert False

    # length is max(#entries, cache_len)
    assert cache.__len__() == case.len

    # make sure the first entry is the one ejected
    if case.cache_len > 1 and case.init:
        assert "one" in cache.keys()
    else:
        assert "one" not in cache.keys()


@pytest.mark.parametrize("method", ["init", "assign"])
def test_cache_overflow_default(method):
    """Test default overflow logic."""
    if method == "init":
        cache = LRUCache([("one", img), ("two", img), ("three", img)], cache_max_bytes=img_size * 2)
    elif method == "assign":
        cache = LRUCache(cache_max_bytes=img_size * 2)
        cache["one"] = img
        cache["two"] = img
        cache["three"] = img
    else:
        assert False

    assert "one" not in cache.keys()
    assert "two" in cache.keys()
    assert "three" in cache.keys()

@pytest.mark.parametrize("mode", ["get", "set"])
@pytest.mark.parametrize("add_third", [False, True])
def test_cache_lru_overflow(mode, add_third):
    img = Image.new('RGB', (100, 100))
    img_size = sys.getsizeof(img.tobytes())

    """Test that key access resets LRU logic."""

    cache = LRUCache([("one", img), ("two", img)], cache_max_bytes=img_size * 2)

    if mode == "get":
        dummy = cache["one"]
    elif mode == "set":
        cache["one"] = img
    else:
        assert False

    if add_third:
        cache["three"] = img

        assert "one" in cache.keys()
        assert "two" not in cache.keys()
        assert "three" in cache.keys()
    else:
        assert "one" in cache.keys()
        assert "two" in cache.keys()
        assert "three" not in cache.keys()


def test_cache_keyerror():
    cache = LRUCache()
    with pytest.raises(KeyError):
        cache["foo"]


def test_cache_miss_doesnt_eject():
    cache = LRUCache([("one", img), ("two", img)], cache_max_bytes=img_size * 3)
    with pytest.raises(KeyError):
        cache["foo"]

    assert len(cache) == 2
    assert "one" in cache.keys()
    assert "two" in cache.keys()

def test_urlencode_url():
    assert urlencode_url("https://www.example.com") == "https://www.example.com"
    assert urlencode_url("https://www.example.com/url%20with%20spaces") == "https://www.example.com/url%20with%20spaces"


def test_batched():
    assert list(batched("", 2)) == []
    assert list(batched("a", 2)) == [["a"]]
    assert list(batched("ab", 2)) == [["a", "b"]]
    assert list(batched("abc", 2)) == [["a", "b"], ["c"]]
    assert list(batched("abcd", 2)) == [["a", "b"], ["c", "d"]]
    assert list(batched("abcde", 2)) == [["a", "b"], ["c", "d"], ["e"]]
    assert list(batched("abcdef", 2)) == [["a", "b"], ["c", "d"], ["e", "f"]]

    with pytest.raises(ValueError):
        list(batched("foo", 0))


def test_parse_datetime():
    # mastodon uses this format
    dt = parse_datetime("2023-07-21T13:27:45.996+00:00")
    assert dt_tuple(dt) == (2023, 7, 21, 13, 27, 45, 0)

    dt = parse_datetime("2023-07-21T13:27:45.996+01:00")
    assert dt_tuple(dt) == (2023, 7, 21, 12, 27, 45, 0)

    dt = parse_datetime("2023-07-21T13:27:45.996-06:00")
    assert dt_tuple(dt) == (2023, 7, 21, 19, 27, 45, 0)

    # snac2 uses this format
    dt = parse_datetime("2023-12-29T09:22:15Z")
    assert dt_tuple(dt) == (2023, 12, 29, 9, 22, 15, 0)


def dt_tuple(dt: datetime):
    assert isinstance(dt, datetime)

    # Parsing should create an aware datetime object
    offset = dt.utcoffset()
    assert offset is not None

    return (
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second,
        offset.total_seconds()
    )
