import webbrowser

import click

from toot import api, config
from toot.auth import get_or_create_app, login_auth_code, login_username_password
from toot.cli import AccountParamType, cli
from toot.cli.diag import print_diag
from toot.cli.validators import validate_instance
from toot.output import print_warning

instance_option = click.option(
    "--instance", "-i", "base_url",
    prompt="Enter instance URL",
    default="https://mastodon.social",
    callback=validate_instance,
    help="""Domain or base URL of the instance to log into,
            e.g. 'mastodon.social' or 'https://mastodon.social'""",
)


@cli.command()
def auth():
    """Show logged in accounts and instances"""
    config_data = config.load_config()

    if not config_data["users"]:
        click.echo("You are not logged in to any accounts")
        return

    active_user = config_data["active_user"]

    click.echo("Authenticated accounts:")
    for uid, u in config_data["users"].items():
        active_label = "ACTIVE" if active_user == uid else ""
        uid = click.style(uid, fg="green")
        active_label = click.style(active_label, fg="yellow")
        click.echo(f"* {uid} {active_label}")

    path = config.get_config_file_path()
    path = click.style(path, "blue")
    click.echo(f"\nAuth tokens are stored in: {path}")


@cli.command(hidden=True)
def env():
    """Deprecated in favour of 'diag'"""
    print_warning("`toot env` is deprecated in favour of `toot diag`")
    click.echo()
    print_diag(False, False)


@cli.command(name="login_cli")
@instance_option
@click.option("--email", "-e", help="Email address to log in with", prompt=True)
@click.option("--password", "-p", hidden=True, prompt=True, hide_input=True)
def login_cli(base_url: str, email: str, password: str):
    """
    Log into an instance from the console (not recommended)

    Does NOT support two factor authentication, may not work on instances
    other than Mastodon, mostly useful for scripting.
    """
    app = get_or_create_app(base_url)
    login_username_password(app, email, password)

    click.secho("✓ Successfully logged in.", fg="green")
    click.echo("Access token saved to config at: ", nl=False)
    click.secho(config.get_config_file_path(), fg="green")


LOGIN_EXPLANATION = """This authentication method requires you to log into your
Mastodon instance in your browser, where you will be asked to authorize toot to
access your account. When you do, you will be given an authorization code which
you need to paste here.""".replace("\n", " ")


@cli.command()
@instance_option
def login(base_url: str):
    """Log into an instance using your browser (recommended)"""
    app = get_or_create_app(base_url)
    url = api.get_browser_login_url(app)

    click.echo(click.wrap_text(LOGIN_EXPLANATION))
    click.echo("\nLogin URL:")
    click.echo(url)

    yesno = click.prompt("Open link in default browser? [Y/n]", default="Y", show_default=False)
    if not yesno or yesno.lower() == 'y':
        webbrowser.open(url)

    authorization_code = ""
    while not authorization_code:
        authorization_code = click.prompt("Authorization code")

    login_auth_code(app, authorization_code)

    click.echo()
    click.secho("✓ Successfully logged in.", fg="green")


@cli.command()
@click.argument("account", type=AccountParamType(), required=False)
def logout(account: str):
    """Log out of ACCOUNT, delete stored access keys"""
    accounts = _get_accounts_list()

    if not account:
        raise click.ClickException(f"Specify account to log out:\n{accounts}")

    user = config.load_user(account)

    if not user:
        raise click.ClickException(f"Account not found. Logged in accounts:\n{accounts}")

    config.delete_user(user)
    click.secho(f"✓ Account {account} logged out", fg="green")


@cli.command()
@click.argument("account", type=AccountParamType(), required=False)
def activate(account: str):
    """Switch to logged in ACCOUNT."""
    accounts = _get_accounts_list()

    if not account:
        raise click.ClickException(f"Specify account to activate:\n{accounts}")

    user = config.load_user(account)

    if not user:
        raise click.ClickException(f"Account not found. Logged in accounts:\n{accounts}")

    config.activate_user(user)
    click.secho(f"✓ Account {account} activated", fg="green")


def _get_accounts_list() -> str:
    accounts = config.load_config()["users"].keys()
    if not accounts:
        raise click.ClickException("You're not logged into any accounts")
    return "\n".join([f"* {acct}" for acct in accounts])
