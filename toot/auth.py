from toot import api, config, User, App
from toot.entities import from_dict, Instance
from toot.exceptions import ApiError, ConsoleError
from urllib.parse import urlparse


def find_instance(base_url: str) -> Instance:
    try:
        instance = api.get_instance(base_url).json()
        return from_dict(Instance, instance)
    except ApiError:
        raise ConsoleError(f"Instance not found at {base_url}")


def register_app(domain: str, base_url: str) -> App:
    try:
        response = api.create_app(base_url)
    except ApiError:
        raise ConsoleError("Registration failed.")

    app = App(domain, base_url, response['client_id'], response['client_secret'])
    config.save_app(app)

    return app


def get_or_create_app(base_url: str) -> App:
    instance = find_instance(base_url)
    domain = _get_instance_domain(instance)
    return config.load_app(domain) or register_app(domain, base_url)


def create_user(app: App, access_token: str) -> User:
    # Username is not yet known at this point, so fetch it from Mastodon
    user = User(app.instance, None, access_token)
    creds = api.verify_credentials(app, user).json()

    user = User(app.instance, creds["username"], access_token)
    config.save_user(user, activate=True)

    return user


def login_username_password(app: App, email: str, password: str) -> User:
    try:
        response = api.login(app, email, password)
    except Exception:
        raise ConsoleError("Login failed")

    return create_user(app, response["access_token"])


def login_auth_code(app: App, authorization_code: str) -> User:
    try:
        response = api.request_access_token(app, authorization_code)
    except Exception:
        raise ConsoleError("Login failed")

    return create_user(app, response["access_token"])


def _get_instance_domain(instance: Instance) -> str:
    """Extracts the instance domain name.

    Pleroma and its forks return an actual URI here, rather than a domain name
    like Mastodon. This is contrary to the spec.¯ in that case, parse out the
    domain and return it.

    TODO: when updating to v2 instance endpoint, this field has been renamed to
    `domain`
    """
    if instance.uri.startswith("http"):
        return urlparse(instance.uri).netloc
    return instance.uri
