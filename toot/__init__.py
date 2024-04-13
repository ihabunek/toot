import os
import sys

from os.path import join, expanduser
from typing import NamedTuple
from importlib import metadata


try:
    __version__ = metadata.version("toot")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0"


class App(NamedTuple):
    instance: str
    base_url: str
    client_id: str
    client_secret: str


class User(NamedTuple):
    instance: str
    username: str
    access_token: str


DEFAULT_INSTANCE = 'https://mastodon.social'

CLIENT_NAME = 'toot - a Mastodon CLI client'
CLIENT_WEBSITE = 'https://github.com/ihabunek/toot'

TOOT_CONFIG_DIR_NAME = "toot"


def get_config_dir():
    """Returns the path to toot config directory"""

    # On Windows, store the config in roaming appdata
    if sys.platform == "win32" and "APPDATA" in os.environ:
        return join(os.getenv("APPDATA"), TOOT_CONFIG_DIR_NAME)

    # Respect XDG_CONFIG_HOME env variable if set
    # https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
    if "XDG_CONFIG_HOME" in os.environ:
        config_home = expanduser(os.environ["XDG_CONFIG_HOME"])
        return join(config_home, TOOT_CONFIG_DIR_NAME)

    # Default to ~/.config/toot/
    return join(expanduser("~"), ".config", TOOT_CONFIG_DIR_NAME)
