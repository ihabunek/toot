import json
import platform
from os import path
from typing import Optional

import click

from toot import __version__, api, config, settings
from toot.cli import cli
from toot.entities import Instance, from_dict
from toot.output import bold, yellow
from toot.utils import get_distro_name, get_version

DIAG_DEPENDENCIES = [
    "beautifulsoup4",
    "click",
    "pillow",
    "requests",
    "setuptools",
    "term-image",
    "tomlkit",
    "typing-extensions",
    "urwid",
    "urwidgets",
    "wcwidth",
]


@cli.command()
@click.option(
    "-f",
    "--files",
    is_flag=True,
    help="Print contents of the config and settings files in diagnostic output",
)
@click.option(
    "-s",
    "--server",
    is_flag=True,
    help="Print information about the curren server in diagnostic output",
)
def diag(files: bool, server: bool):
    """Display useful information for diagnosing problems"""
    print_diag(files, server)


def print_diag(files: bool, server: bool):
    instance: Optional[Instance] = None
    if server:
        _, app = config.get_active_user_app()
        if app:
            response = api.get_instance(app.base_url)
            instance = from_dict(Instance, response.json())

    click.echo("## Toot Diagnostics")
    print_environment()
    print_dependencies()
    print_instance(instance)
    print_settings(files)
    print_config(files)


def print_environment():
    click.echo()
    click.echo(f"toot {__version__}")
    click.echo(f"Python {platform.python_version()}")
    click.echo(platform.platform())

    distro = get_distro_name()
    if distro:
        click.echo(distro)


def print_dependencies():
    click.echo()
    click.secho(bold("Dependencies:"))
    for dep in DIAG_DEPENDENCIES:
        version = get_version(dep) or yellow("not installed")
        click.echo(f" * {dep}: {version}")


def print_instance(instance: Optional[Instance]):
    if instance:
        click.echo()
        click.echo(bold("Server:"))
        click.echo(instance.title)
        click.echo(instance.uri)
        click.echo(f"version {instance.version}")


def print_settings(include_files: bool):
    click.echo()
    settings_path = settings.get_settings_path()
    if path.exists(settings_path):
        click.echo(f"Settings file: {settings_path}")
        if include_files:
            with open(settings_path, "r") as f:
                click.echo("\n```toml")
                click.echo(f.read().strip())
                click.echo("```\n")
    else:
        click.echo(f'Settings file: {yellow("not found")}')


def print_config(include_files: bool):
    click.echo()
    config_path = config.get_config_file_path()
    if path.exists(config_path):
        click.echo(f"Config file: {config_path}")
        if include_files:
            content = _get_anonymized_config(config_path)
            click.echo("\n```json")
            click.echo(json.dumps(content, indent=4))
            click.echo("```\n")
    else:
        click.echo(f'Config file: {yellow("not found")}')


def _get_anonymized_config(config_path):
    with open(config_path, "r") as f:
        content = json.load(f)

        for app in content.get("apps", {}).values():
            app["client_id"] = "*****"
            app["client_secret"] = "*****"

        for user in content.get("users", {}).values():
            user["access_token"] = "*****"

        return content
