import os
import sys

from os.path import join, expanduser
from collections import namedtuple

__version__ = '0.39.0'

App = namedtuple('App', ['instance', 'base_url', 'client_id', 'client_secret'])
User = namedtuple('User', ['instance', 'username', 'access_token'])

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
