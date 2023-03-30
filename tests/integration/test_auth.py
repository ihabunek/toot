from tests.integration.conftest import TRUMPET
from toot import api
from toot.utils import get_text


def test_update_account_no_options(run):
    out = run("update_account")
    assert out == "Please specify at least one option to update the account"


def test_update_account_display_name(run, app, user):
    out = run("update_account", "--display-name", "elwood")
    assert out == "✓ Account updated"

    account = api.verify_credentials(app, user)
    assert account["display_name"] == "elwood"


def test_update_account_note(run, app, user):
    note = ("It's 106 miles to Chicago, we got a full tank of gas, half a pack "
           "of cigarettes, it's dark... and we're wearing sunglasses.")

    out = run("update_account", "--note", note)
    assert out == "✓ Account updated"

    account = api.verify_credentials(app, user)
    assert get_text(account["note"]) == note


def test_update_account_language(run, app, user):
    out = run("update_account", "--language", "hr")
    assert out == "✓ Account updated"

    account = api.verify_credentials(app, user)
    assert account["source"]["language"] == "hr"


def test_update_account_privacy(run, app, user):
    out = run("update_account", "--privacy", "private")
    assert out == "✓ Account updated"

    account = api.verify_credentials(app, user)
    assert account["source"]["privacy"] == "private"


def test_update_account_avatar(run, app, user):
    account = api.verify_credentials(app, user)
    old_value = account["avatar"]

    out = run("update_account", "--avatar", TRUMPET)
    assert out == "✓ Account updated"

    account = api.verify_credentials(app, user)
    assert account["avatar"] != old_value


def test_update_account_header(run, app, user):
    account = api.verify_credentials(app, user)
    old_value = account["header"]

    out = run("update_account", "--header", TRUMPET)
    assert out == "✓ Account updated"

    account = api.verify_credentials(app, user)
    assert account["header"] != old_value


def test_update_account_locked(run, app, user):
    out = run("update_account", "--locked")
    assert out == "✓ Account updated"

    account = api.verify_credentials(app, user)
    assert account["locked"] is True

    out = run("update_account", "--no-locked")
    assert out == "✓ Account updated"

    account = api.verify_credentials(app, user)
    assert account["locked"] is False


def test_update_account_bot(run, app, user):
    out = run("update_account", "--bot")
    assert out == "✓ Account updated"

    account = api.verify_credentials(app, user)
    assert account["bot"] is True

    out = run("update_account", "--no-bot")
    assert out == "✓ Account updated"

    account = api.verify_credentials(app, user)
    assert account["bot"] is False


def test_update_account_discoverable(run, app, user):
    out = run("update_account", "--discoverable")
    assert out == "✓ Account updated"

    account = api.verify_credentials(app, user)
    assert account["discoverable"] is True

    out = run("update_account", "--no-discoverable")
    assert out == "✓ Account updated"

    account = api.verify_credentials(app, user)
    assert account["discoverable"] is False


def test_update_account_sensitive(run, app, user):
    out = run("update_account", "--sensitive")
    assert out == "✓ Account updated"

    account = api.verify_credentials(app, user)
    assert account["source"]["sensitive"] is True

    out = run("update_account", "--no-sensitive")
    assert out == "✓ Account updated"

    account = api.verify_credentials(app, user)
    assert account["source"]["sensitive"] is False
