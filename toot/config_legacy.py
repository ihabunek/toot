# -*- coding: utf-8 -*-

import os

from . import User, App

# The dir where all toot configuration is stored
CONFIG_DIR = os.environ['HOME'] + '/.config/toot/'

# Subfolder where application access keys for various instances are stored
INSTANCES_DIR = CONFIG_DIR + 'instances/'

# File in which user access token is stored
CONFIG_USER_FILE = CONFIG_DIR + 'user.cfg'


def load_user(path):
    if not os.path.exists(path):
        return None

    with open(path, 'r') as f:
        lines = f.read().split()
        try:
            return User(*lines)
        except TypeError:
            return None


def load_apps(path):
    if not os.path.exists(path):
        return []

    for name in os.listdir(path):
        with open(path + name) as f:
            values = f.read().split()
            try:
                yield App(*values)
            except TypeError:
                pass


def add_username(user, apps):
    """When using broser login, username was not stored so look it up"""
    if not user:
        return None

    apps = [a for a in apps if a.instance == user.instance]

    if not apps:
        return None

    from toot.api import verify_credentials
    creds = verify_credentials(apps.pop(), user)

    return User(user.instance, creds['username'], user.access_token)


def load_legacy_config():
    apps = list(load_apps(INSTANCES_DIR))
    user = load_user(CONFIG_USER_FILE)
    user = add_username(user, apps)

    return apps, user
