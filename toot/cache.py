import os
import sys

from pathlib import Path
from typing import Optional

from toot import App, User

CACHE_SUBFOLDER = "toot"


def save_last_post_id(app: App, user: User, id: str) -> None:
    """Save ID of the last post posted to this instance"""
    path = _last_post_id_path(app, user)
    with open(path, "w") as f:
        f.write(id)


def get_last_post_id(app: App, user: User) -> Optional[str]:
    """Retrieve ID of the last post posted to this instance"""
    path = _last_post_id_path(app, user)
    if path.exists():
        with open(path, "r") as f:
            return f.read()


def clear_last_post_id(app: App, user: User) -> None:
    """Delete the cached last post ID for this instance"""
    path = _last_post_id_path(app, user)
    path.unlink(missing_ok=True)


def _last_post_id_path(app: App, user: User):
    return get_cache_dir("last_post_ids") / f"{user.username}_{app.instance}"


def get_cache_dir(subdir: Optional[str] = None) -> Path:
    path = _cache_dir_path()
    if subdir:
        path = path / subdir
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cache_dir_path() -> Path:
    """Returns the path to the cache directory"""

    # Windows
    if sys.platform == "win32" and "LOCALAPPDATA" in os.environ:
        return Path(os.environ["LOCALAPPDATA"], CACHE_SUBFOLDER)

    # Mac OS
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / CACHE_SUBFOLDER

    # Respect XDG_CONFIG_HOME env variable if set
    # https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
    if "XDG_CACHE_HOME" in os.environ:
        return Path(os.environ["XDG_CACHE_HOME"], CACHE_SUBFOLDER)

    return Path.home() / ".cache" / CACHE_SUBFOLDER
