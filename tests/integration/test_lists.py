from tests.integration.conftest import register_account


def test_lists_empty(run):
    out = run("lists")
    assert out == "You have no lists defined."


def test_list_create_delete(run):
    out = run("list_create", "banana")
    assert out == '✓ List "banana" created.'

    out = run("lists")
    assert "banana" in out

    out = run("list_create", "mango")
    assert out == '✓ List "mango" created.'

    out = run("lists")
    assert "banana" in out
    assert "mango" in out

    out = run("list_delete", "banana")
    assert out == '✓ List "banana" deleted.'

    out = run("lists")
    assert "banana" not in out
    assert "mango" in out

    out = run("list_delete", "mango")
    assert out == '✓ List "mango" deleted.'

    out = run("lists")
    assert out == "You have no lists defined."

    out = run("list_delete", "mango")
    assert out == "List not found"


def test_list_add_remove(run, app):
    acc = register_account(app)
    run("list_create", "foo")

    out = run("list_add", "foo", acc.username)
    assert out == f"You must follow @{acc.username} before adding this account to a list."

    run("follow", acc.username)

    out = run("list_add", "foo", acc.username)
    assert out == f'✓ Added account "{acc.username}"'

    out = run("list_accounts", "foo")
    assert acc.username in out

    # Account doesn't exist
    out = run("list_add", "foo", "does_not_exist")
    assert out == "Account not found"

    # List doesn't exist
    out = run("list_add", "does_not_exist", acc.username)
    assert out == "List not found"

    out = run("list_remove", "foo", acc.username)
    assert out == f'✓ Removed account "{acc.username}"'

    out = run("list_accounts", "foo")
    assert out == "This list has no accounts."
