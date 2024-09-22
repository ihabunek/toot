from uuid import uuid4
from tests.integration.conftest import TRUMPET, assert_ok
from toot import api, cli
from toot.entities import Account, from_dict
from toot.utils import get_text


def test_update_account_no_options(run):
    result = run(cli.accounts.update_account)
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: Please specify at least one option to update the account"


def test_update_account_display_name(run, app, user):
    name = str(uuid4())[:10]

    result = run(cli.accounts.update_account, "--display-name", name)
    assert_ok(result)
    assert result.stdout.strip() == "✓ Account updated"

    account = api.verify_credentials(app, user).json()
    assert account["display_name"] == name


def test_update_account_json(run_json, app, user):
    name = str(uuid4())[:10]
    out = run_json(cli.accounts.update_account, "--display-name", name, "--json")
    account = from_dict(Account, out)
    assert account.acct == user.username
    assert account.display_name == name


def test_update_account_note(run, app, user):
    note = ("It's 106 miles to Chicago, we got a full tank of gas, half a pack "
           "of cigarettes, it's dark... and we're wearing sunglasses.")

    result = run(cli.accounts.update_account, "--note", note)
    assert_ok(result)
    assert result.stdout.strip() == "✓ Account updated"

    account = api.verify_credentials(app, user).json()
    assert get_text(account["note"]) == note


def test_update_account_language(run, app, user):
    result = run(cli.accounts.update_account, "--language", "hr")
    assert_ok(result)
    assert result.stdout.strip() == "✓ Account updated"

    account = api.verify_credentials(app, user).json()
    assert account["source"]["language"] == "hr"


def test_update_account_privacy(run, app, user):
    result = run(cli.accounts.update_account, "--privacy", "private")
    assert_ok(result)
    assert result.stdout.strip() == "✓ Account updated"

    account = api.verify_credentials(app, user).json()
    assert account["source"]["privacy"] == "private"


def test_update_account_avatar(run, app, user):
    account = api.verify_credentials(app, user).json()
    old_value = account["avatar"]

    result = run(cli.accounts.update_account, "--avatar", TRUMPET)
    assert_ok(result)
    assert result.stdout.strip() == "✓ Account updated"

    account = api.verify_credentials(app, user).json()
    assert account["avatar"] != old_value


def test_update_account_header(run, app, user):
    account = api.verify_credentials(app, user).json()
    old_value = account["header"]

    result = run(cli.accounts.update_account, "--header", TRUMPET)
    assert_ok(result)
    assert result.stdout.strip() == "✓ Account updated"

    account = api.verify_credentials(app, user).json()
    assert account["header"] != old_value


def test_update_account_locked(run, app, user):
    result = run(cli.accounts.update_account, "--locked")
    assert_ok(result)
    assert result.stdout.strip() == "✓ Account updated"

    account = api.verify_credentials(app, user).json()
    assert account["locked"] is True

    result = run(cli.accounts.update_account, "--no-locked")
    assert_ok(result)
    assert result.stdout.strip() == "✓ Account updated"

    account = api.verify_credentials(app, user).json()
    assert account["locked"] is False


def test_update_account_bot(run, app, user):
    result = run(cli.accounts.update_account, "--bot")

    assert_ok(result)
    assert result.stdout.strip() == "✓ Account updated"

    account = api.verify_credentials(app, user).json()
    assert account["bot"] is True

    result = run(cli.accounts.update_account, "--no-bot")
    assert_ok(result)
    assert result.stdout.strip() == "✓ Account updated"

    account = api.verify_credentials(app, user).json()
    assert account["bot"] is False


def test_update_account_discoverable(run, app, user):
    result = run(cli.accounts.update_account, "--discoverable")
    assert_ok(result)
    assert result.stdout.strip() == "✓ Account updated"

    account = api.verify_credentials(app, user).json()
    assert account["discoverable"] is True

    result = run(cli.accounts.update_account, "--no-discoverable")
    assert_ok(result)
    assert result.stdout.strip() == "✓ Account updated"

    account = api.verify_credentials(app, user).json()
    assert account["discoverable"] is False


def test_update_account_sensitive(run, app, user):
    result = run(cli.accounts.update_account, "--sensitive")
    assert_ok(result)
    assert result.stdout.strip() == "✓ Account updated"

    account = api.verify_credentials(app, user).json()
    assert account["source"]["sensitive"] is True

    result = run(cli.accounts.update_account, "--no-sensitive")
    assert_ok(result)
    assert result.stdout.strip() == "✓ Account updated"

    account = api.verify_credentials(app, user).json()
    assert account["source"]["sensitive"] is False
