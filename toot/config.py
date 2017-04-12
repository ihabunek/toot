import os

from . import User, App

CONFIG_DIR = os.environ['HOME'] + '/.config/toot/'
CONFIG_APP_FILE = CONFIG_DIR + 'app.cfg'
CONFIG_USER_FILE = CONFIG_DIR + 'user.cfg'


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
        return f.write("\n".join(values))


def load_app():
    return _load(CONFIG_APP_FILE, App)


def load_user():
    return _load(CONFIG_USER_FILE, User)


def save_app(app):
    return _save(CONFIG_APP_FILE, app)


def save_user(user):
    return _save(CONFIG_USER_FILE, user)


def delete_app(app):
    return os.unlink(CONFIG_APP_FILE)


def delete_user(user):
    return os.unlink(CONFIG_USER_FILE)
