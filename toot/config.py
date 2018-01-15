# -*- coding: utf-8 -*-

import os
import json

from functools import wraps
from os.path import dirname

from toot import User, App
from toot.config_legacy import load_legacy_config
from toot.exceptions import ConsoleError
from toot.output import print_out


def get_config_file_path():
    """Returns the path to toot config file

    Attempts to locate config home dir from XDG_CONFIG_HOME env variable.
    See: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html#variables
    If not found, defaults to `~/.config`.
    """
    config_dir = os.getenv('XDG_CONFIG_HOME', '~/.config')
    return os.path.expanduser(config_dir + '/toot/config.json')


CONFIG_FILE = get_config_file_path()


def user_id(user):
    return "{}@{}".format(user.username, user.instance)


def make_config(path):
    """Creates a config file.

    Attempts to load data from legacy config files if they exist.
    """
    apps, user = load_legacy_config()

    apps = {a.instance: a._asdict() for a in apps}
    users = {user_id(user): user._asdict()} if user else {}
    active_user = user_id(user) if user else None

    config = {
        "apps": apps,
        "users": users,
        "active_user": active_user,
    }

    print_out("Creating config file at <blue>{}</blue>".format(path))

    # Ensure dir exists
    os.makedirs(dirname(path), exist_ok=True)

    with open(path, 'w') as f:
        json.dump(config, f, indent=True)


def load_config():
    if not os.path.exists(CONFIG_FILE):
        make_config(CONFIG_FILE)

    with open(CONFIG_FILE) as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        return json.dump(config, f, indent=True)


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
