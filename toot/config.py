import json
import os

from contextlib import contextmanager
from os.path import dirname, join
from typing import Optional

from toot import User, App, get_config_dir
from toot.exceptions import ConsoleError


TOOT_CONFIG_FILE_NAME = "config.json"


def get_config_file_path():
    """Returns the path to toot config file."""
    return join(get_config_dir(), TOOT_CONFIG_FILE_NAME)


def user_id(user: User):
    return "{}@{}".format(user.username, user.instance)


def make_config(path: str):
    """Creates an empty toot configuration file."""
    config = {
        "apps": {},
        "users": {},
        "active_user": None,
    }

    # Ensure dir exists
    os.makedirs(dirname(path), exist_ok=True)

    # Create file with 600 permissions since it contains secrets
    fd = os.open(path, os.O_CREAT | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump(config, f, indent=True)


def load_config():
    # Just to prevent accidentally running tests on production
    if os.environ.get("TOOT_TESTING"):
        raise Exception("Tests should not access the config file!")

    path = get_config_file_path()

    if not os.path.exists(path):
        make_config(path)

    with open(path) as f:
        return json.load(f)


def save_config(config):
    path = get_config_file_path()
    with open(path, "w") as f:
        return json.dump(config, f, indent=True, sort_keys=True)


def extract_user_app(config, user_id: str):
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


def get_user_app(user_id: str):
    """Returns (User, App) for given user ID or (None, None) if user is not logged in."""
    return extract_user_app(load_config(), user_id)


def load_app(instance: str) -> Optional[App]:
    config = load_config()
    if instance in config['apps']:
        return App(**config['apps'][instance])


def load_user(user_id: str, throw=False):
    config = load_config()

    if user_id in config['users']:
        return User(**config['users'][user_id])

    if throw:
        raise ConsoleError("User '{}' not found".format(user_id))


def get_user_list():
    config = load_config()
    return config['users']


@contextmanager
def edit_config():
    config = load_config()
    yield config
    save_config(config)


def save_app(app: App):
    with edit_config() as config:
        config['apps'][app.instance] = app._asdict()


def delete_app(config, app: App):
    with edit_config() as config:
        config['apps'].pop(app.instance, None)


def save_user(user: User, activate=True):
    with edit_config() as config:
        config['users'][user_id(user)] = user._asdict()

        if activate:
            config['active_user'] = user_id(user)


def delete_user(user: User):
    with edit_config() as config:
        config['users'].pop(user_id(user), None)

        if config['active_user'] == user_id(user):
            config['active_user'] = None


def activate_user(user: User):
    with edit_config() as config:
        config['active_user'] = user_id(user)
