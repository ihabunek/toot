# -*- coding: utf-8 -*-

import os

from . import User, App

# The dir where all toot configuration is stored
CONFIG_DIR = os.environ['HOME'] + '/.config/toot/'

# Subfolder where application access keys for various instances are stored
INSTANCES_DIR = CONFIG_DIR + 'instances/'

# File in which user access token is stored
CONFIG_USER_FILE = CONFIG_DIR + 'user.cfg'


def get_instance_config_path(instance):
    return INSTANCES_DIR + instance


def get_user_config_path():
    return CONFIG_USER_FILE


def _load(file, tuple_class):
    if not os.path.exists(file):
        return None

    with open(file, 'r') as f:
        lines = f.read().split()
        try:
            return tuple_class(*lines)
        except TypeError:
            return None


def _save(file, named_tuple):
    directory = os.path.dirname(file)
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(file, 'w') as f:
        values = [v for v in named_tuple]
        f.write("\n".join(values))


def load_app(instance):
    path = get_instance_config_path(instance)
    return _load(path, App)


def load_user():
    path = get_user_config_path()
    return _load(path, User)


def save_app(app):
    path = get_instance_config_path(app.instance)
    _save(path, app)
    return path


def save_user(user):
    path = get_user_config_path()
    _save(path, user)
    return path


def delete_app(instance):
    path = get_instance_config_path(instance)
    os.unlink(path)
    return path


def delete_user():
    path = get_user_config_path()
    os.unlink(path)
    return path
