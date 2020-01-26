import json
import os
import sys

from functools import wraps
from os.path import dirname, join, expanduser

from toot import User, App
from toot.exceptions import ConsoleError
from toot.output import print_out


TOOT_CONFIG_DIR_NAME = "toot"
TOOT_CONFIG_FILE_NAME = "config.json"


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


def get_config_file_path():
    """Returns the path to toot config file."""
    return join(get_config_dir(), TOOT_CONFIG_FILE_NAME)


CONFIG_FILE = get_config_file_path()


def user_id(user):
    return "{}@{}".format(user.username, user.instance)


def make_config(path):
    """Creates an empty toot configuration file."""
    config = {
        "apps": {},
        "users": {},
        "active_user": None,
    }

    print_out("Creating config file at <blue>{}</blue>".format(path))

    # Ensure dir exists
    os.makedirs(dirname(path), exist_ok=True)

    # Create file with 600 permissions since it contains secrets
    fd = os.open(path, os.O_CREAT | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump(config, f, indent=True)


def load_config():
    if not os.path.exists(CONFIG_FILE):
        make_config(CONFIG_FILE)

    with open(CONFIG_FILE) as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        return json.dump(config, f, indent=True, sort_keys=True)


def extract_user_app(config, user_id):
    if user_id not in config['users']:
        return None, None

    user_data = config['users'][user_id]
    instance = user_data['instance']

    if instance not in config['apps']:
        return None, None

    app_data = config['apps'][instance]
    return User(**user_data), App(**app_data)


def get_active_user_app():
    """Returns (User, App) of active user or (None, None) if no user is active."""
    config = load_config()

    if config['active_user']:
        return extract_user_app(config, config['active_user'])

    return None, None


def get_user_app(user_id):
    """Returns (User, App) for given user ID or (None, None) if user is not logged in."""
    return extract_user_app(load_config(), user_id)


def load_app(instance):
    config = load_config()
    if instance in config['apps']:
        return App(**config['apps'][instance])


def load_user(user_id, throw=False):
    config = load_config()

    if user_id in config['users']:
        return User(**config['users'][user_id])

    if throw:
        raise ConsoleError("User '{}' not found".format(user_id))


def modify_config(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        config = load_config()
        config = f(config, *args, **kwargs)
        save_config(config)
        return config

    return wrapper


@modify_config
def save_app(config, app):
    assert isinstance(app, App)

    config['apps'][app.instance] = app._asdict()

    return config


@modify_config
def delete_app(config, app):
    assert isinstance(app, App)

    config['apps'].pop(app.instance, None)

    return config


@modify_config
def save_user(config, user, activate=True):
    assert isinstance(user, User)

    config['users'][user_id(user)] = user._asdict()

    if activate:
        config['active_user'] = user_id(user)

    return config


@modify_config
def delete_user(config, user):
    assert isinstance(user, User)

    config['users'].pop(user_id(user), None)

    if config['active_user'] == user_id(user):
        config['active_user'] = None

    return config


@modify_config
def activate_user(config, user):
    assert isinstance(user, User)

    config['active_user'] = user_id(user)

    return config
