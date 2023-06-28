import os
import sys

from functools import lru_cache
from os.path import exists, join
from tomlkit import parse
from toot.config import get_config_dir
from typing import Optional, Type


TOOT_SETTINGS_FILE_NAME = "settings.toml"


def get_settings_path():
    return join(get_config_dir(), TOOT_SETTINGS_FILE_NAME)


SETTINGS_FILE = get_settings_path()


def load_settings() -> dict:
    if not exists(SETTINGS_FILE):
        return {}

    with open(SETTINGS_FILE) as f:
        return parse(f.read())


@lru_cache(maxsize=None)
def get_settings():
    return load_settings()


def get_setting(key: str, type: Type, default=None):
    """
    Get a setting value. The key should be a dot-separated string,
    e.g. "commands.post.editor" which will correspond to the "editor" setting
    inside the `[commands.post]` section.
    """
    settings = get_settings()
    return _get_setting(settings, key.split("."), type, default)


def _get_setting(dct, keys, type: Type, default=None):
    if len(keys) == 0:
        if isinstance(dct, type):
            return dct
        else:
            # TODO: warn? cast? both?
            return default

    key = keys[0]
    if isinstance(dct, dict) and key in dct:
        return _get_setting(dct[key], keys[1:], type, default)

    return default


def get_debug() -> bool:
    if "--debug" in sys.argv:
        return True

    return get_setting("common.debug", bool, False)


def get_debug_file() -> Optional[str]:
    from_env = os.getenv("TOOT_LOG_FILE")
    if from_env:
        return from_env

    return get_setting("common.debug_file", str)
