from uuid import uuid4
from toot import cli

from tests.integration.conftest import assert_ok, register_account


def test_lists_empty(run):
    result = run(cli.lists.list)
    assert_ok(result)
    assert result.stdout.strip() == "You have no lists defined."


def test_lists_empty_json(run_json):
    lists = run_json(cli.lists.list, "--json")
    assert lists == []


def test_list_create_delete(run):
    result = run(cli.lists.create, "banana")
    assert_ok(result)
    assert result.stdout.strip() == '✓ List "banana" created.'

    result = run(cli.lists.list)
    assert_ok(result)
    assert "banana" in result.stdout

    result = run(cli.lists.create, "mango")
    assert_ok(result)
    assert result.stdout.strip() == '✓ List "mango" created.'

    result = run(cli.lists.list)
    assert_ok(result)
    assert "banana" in result.stdout
    assert "mango" in result.stdout

    result = run(cli.lists.delete, "banana")
    assert_ok(result)
    assert result.stdout.strip() == '✓ List "banana" deleted.'

    result = run(cli.lists.list)
    assert_ok(result)
    assert "banana" not in result.stdout
    assert "mango" in result.stdout

    result = run(cli.lists.delete, "mango")
    assert_ok(result)
    assert result.stdout.strip() == '✓ List "mango" deleted.'

    result = run(cli.lists.list)
    assert_ok(result)
    assert result.stdout.strip() == "You have no lists defined."

    result = run(cli.lists.delete, "mango")
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: List not found"


def test_list_create_delete_json(run, run_json):
    result = run_json(cli.lists.list, "--json")
    assert result == []

    list = run_json(cli.lists.create, "banana", "--json")
    assert list["title"] == "banana"

    [list] = run_json(cli.lists.list, "--json")
    assert list["title"] == "banana"

    list = run_json(cli.lists.create, "mango", "--json")
    assert list["title"] == "mango"

    lists = run_json(cli.lists.list, "--json")
    [list1, list2] = sorted(lists, key=lambda l: l["title"])
    assert list1["title"] == "banana"
    assert list2["title"] == "mango"

    result = run_json(cli.lists.delete, "banana", "--json")
    assert result == {}

    [list] = run_json(cli.lists.list, "--json")
    assert list["title"] == "mango"

    result = run_json(cli.lists.delete, "mango", "--json")
    assert result == {}

    result = run_json(cli.lists.list, "--json")
    assert result == []

    result = run(cli.lists.delete, "mango", "--json")
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: List not found"


def test_list_add_remove(run, app):
    list_name = str(uuid4())
    acc = register_account(app)
    run(cli.lists.create, list_name)

    result = run(cli.lists.add, list_name, acc.username)
    assert result.exit_code == 1
    assert result.stderr.strip() == f"Error: You must follow @{acc.username} before adding this account to a list."

    run(cli.accounts.follow, acc.username)

    result = run(cli.lists.add, list_name, acc.username)
    assert_ok(result)
    assert result.stdout.strip() == f'✓ Added account "{acc.username}"'

    result = run(cli.lists.accounts, list_name)
    assert_ok(result)
    assert acc.username in result.stdout

    # Account doesn't exist
    result = run(cli.lists.add, list_name, "does_not_exist")
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: Account not found"

    # List doesn't exist
    result = run(cli.lists.add, "does_not_exist", acc.username)
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: List not found"

    result = run(cli.lists.remove, list_name, acc.username)
    assert_ok(result)
    assert result.stdout.strip() == f'✓ Removed account "{acc.username}"'

    result = run(cli.lists.accounts, list_name)
    assert_ok(result)
    assert result.stdout.strip() == "This list has no accounts."


def test_list_add_remove_json(run, run_json, app):
    list_name = str(uuid4())
    acc = register_account(app)
    run(cli.lists.create, list_name)

    result = run(cli.lists.add, list_name, acc.username, "--json")
    assert result.exit_code == 1
    assert result.stderr.strip() == f"Error: You must follow @{acc.username} before adding this account to a list."

    run(cli.accounts.follow, acc.username)

    result = run_json(cli.lists.add, list_name, acc.username, "--json")
    assert result == {}

    [account] = run_json(cli.lists.accounts, list_name, "--json")
    assert account["username"] == acc.username

    # Account doesn't exist
    result = run(cli.lists.add, list_name, "does_not_exist", "--json")
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: Account not found"

    # List doesn't exist
    result = run(cli.lists.add, "does_not_exist", acc.username, "--json")
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: List not found"

    result = run_json(cli.lists.remove, list_name, acc.username, "--json")
    assert result == {}

    result = run_json(cli.lists.accounts, list_name, "--json")
    assert result == []
