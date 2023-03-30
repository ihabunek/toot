

def test_whoami(user, run):
    out = run("whoami")
    # TODO: test other fields once updating account is supported
    assert f"@{user.username}" in out


def test_whois(app, friend, run):
    variants = [
        friend.username,
        f"@{friend.username}",
        f"{friend.username}@{app.instance}",
        f"@{friend.username}@{app.instance}",
    ]

    for username in variants:
        out = run("whois", username)
        assert f"@{friend.username}" in out
