import toot
from pkg_resources import get_distribution


def test_version():
    """Version specified in __version__ should be the same as the one
    specified in setup.py."""
    assert toot.__version__ == get_distribution('toot').version
