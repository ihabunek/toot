import sys
import webbrowser

from builtins import input
from getpass import getpass

from toot import api, config, DEFAULT_INSTANCE, User, App
from toot.exceptions import ApiError, ConsoleError
from toot.output import print_out
from urllib.parse import urlparse


def register_app(domain, base_url):
    try:
        print_out("Registering application...")
        response = api.create_app(base_url)
    except ApiError:
        raise ConsoleError("Registration failed.")

    app = App(domain, base_url, response['client_id'], response['client_secret'])
    config.save_app(app)

    print_out("Application tokens saved.")

    return app


def create_app_interactive(base_url):
    if not base_url:
        print_out(f"Enter instance URL [<green>{DEFAULT_INSTANCE}</green>]: ", end="")
        base_url = input()
        if not base_url:
            base_url = DEFAULT_INSTANCE

    domain = get_instance_domain(base_url)

    return config.load_app(domain) or register_app(domain, base_url)


def get_instance_domain(base_url):
    print_out("Looking up instance info...")

    instance = api.get_instance(base_url).json()

    print_out(
        f"Found instance <blue>{instance['title']}</blue> "
        f"running Mastodon version <yellow>{instance['version']}</yellow>"
    )

    # Pleroma and its forks return an actual URI here, rather than a
    # domain name like Mastodon. This is contrary to the spec.¯
    # in that case, parse out the domain and return it.

    parsed_uri = urlparse(instance["uri"])

    if parsed_uri.netloc:
        # Pleroma, Akkoma, GotoSocial, etc.
        return parsed_uri.netloc
    else:
        # Others including Mastodon servers
        return parsed_uri.path

    # NB: when updating to v2 instance endpoint, this field has been renamed to `domain`


def create_user(app, access_token):
    # Username is not yet known at this point, so fetch it from Mastodon
    user = User(app.instance, None, access_token)
    creds = api.verify_credentials(app, user).json()

    user = User(app.instance, creds['username'], access_token)
    config.save_user(user, activate=True)

    print_out("Access token saved to config at: <green>{}</green>".format(
        config.get_config_file_path()))

    return user


def login_interactive(app, email=None):
    print_out("Log in to <green>{}</green>".format(app.instance))

    if email:
        print_out("Email: <green>{}</green>".format(email))

    while not email:
        email = input('Email: ')

    # Accept password piped from stdin, useful for testing purposes but not
    # documented so people won't get ideas. Otherwise prompt for password.
    if sys.stdin.isatty():
        password = getpass('Password: ')
    else:
        password = sys.stdin.read().strip()
        print_out("Password: <green>read from stdin</green>")

    try:
        print_out("Authenticating...")
        response = api.login(app, email, password)
    except ApiError:
        raise ConsoleError("Login failed")

    return create_user(app, response['access_token'])


BROWSER_LOGIN_EXPLANATION = """
This authentication method requires you to log into your Mastodon instance
in your browser, where you will be asked to authorize <yellow>toot</yellow> to access
your account. When you do, you will be given an <yellow>authorization code</yellow>
which you need to paste here.
"""


def login_browser_interactive(app):
    url = api.get_browser_login_url(app)
    print_out(BROWSER_LOGIN_EXPLANATION)

    print_out("This is the login URL:")
    print_out(url)
    print_out("")

    yesno = input("Open link in default browser? [Y/n]")
    if not yesno or yesno.lower() == 'y':
        webbrowser.open(url)

    authorization_code = ""
    while not authorization_code:
        authorization_code = input("Authorization code: ")

    print_out("\nRequesting access token...")
    response = api.request_access_token(app, authorization_code)

    return create_user(app, response['access_token'])
