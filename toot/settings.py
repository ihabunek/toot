import configparser
import os
from os.path import join

from toot.config import get_config_dir

TOOT_SETTINGS_FILE_NAME = "settings.ini"

DEAFAULT_SETTINGS = {

}

def get_config_file_path():
    """Returns the path to toot config file."""
    return join(get_config_dir(), TOOT_SETTINGS_FILE_NAME)


def load_settings():
    path = get_config_file_path()
    if not os.path.exists(path):
        return

    config = configparser.ConfigParser()
    with open(path, "r") as f:
        config.read_file(f)
    return config

print("loading")
settings = load_settings()
