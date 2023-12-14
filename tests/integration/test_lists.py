from toot import cli

from tests.integration.conftest import register_account


def test_lists_empty(run):
    result = run(cli.lists.list)
    assert result.exit_code == 0
    assert result.stdout.strip() == "You have no lists defined."


def test_list_create_delete(run):
    result = run(cli.lists.create, "banana")
    assert result.exit_code == 0
    assert result.stdout.strip() == '✓ List "banana" created.'

    result = run(cli.lists.list)
    assert result.exit_code == 0
    assert "banana" in result.stdout

    result = run(cli.lists.create, "mango")
    assert result.exit_code == 0
    assert result.stdout.strip() == '✓ List "mango" created.'

    result = run(cli.lists.list)
    assert result.exit_code == 0
    assert "banana" in result.stdout
    assert "mango" in result.stdout

    result = run(cli.lists.delete, "banana")
    assert result.exit_code == 0
    assert result.stdout.strip() == '✓ List "banana" deleted.'

    result = run(cli.lists.list)
    assert result.exit_code == 0
    assert "banana" not in result.stdout
    assert "mango" in result.stdout

    result = run(cli.lists.delete, "mango")
    assert result.exit_code == 0
    assert result.stdout.strip() == '✓ List "mango" deleted.'

    result = run(cli.lists.list)
    assert result.exit_code == 0
    assert result.stdout.strip() == "You have no lists defined."

    result = run(cli.lists.delete, "mango")
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: List not found"


def test_list_add_remove(run, app):
    acc = register_account(app)
    run(cli.lists.create, "foo")

    result = run(cli.lists.add, "foo", acc.username)
    assert result.exit_code == 1
    assert result.stderr.strip() == f"Error: You must follow @{acc.username} before adding this account to a list."

    run(cli.accounts.follow, acc.username)

    result = run(cli.lists.add, "foo", acc.username)
    assert result.exit_code == 0
    assert result.stdout.strip() == f'✓ Added account "{acc.username}"'

    result = run(cli.lists.accounts, "foo")
    assert result.exit_code == 0
    assert acc.username in result.stdout

    # Account doesn't exist
    result = run(cli.lists.add, "foo", "does_not_exist")
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: Account not found"

    # List doesn't exist
    result = run(cli.lists.add, "does_not_exist", acc.username)
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: List not found"

    result = run(cli.lists.remove, "foo", acc.username)
    assert result.exit_code == 0
    assert result.stdout.strip() == f'✓ Removed account "{acc.username}"'

    result = run(cli.lists.accounts, "foo")
    assert result.exit_code == 0
    assert result.stdout.strip() == "This list has no accounts."
