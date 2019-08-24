from datetime import datetime
from collections import namedtuple


Author = namedtuple("Author", ["account", "display_name"])


def get_author(data, instance):
    # Show the author, not the persopn who reblogged
    status = data["reblog"] or data
    acct = status['account']['acct']
    acct = acct if "@" in acct else "{}@{}".format(acct, instance)
    return Author(acct, status['account']['display_name'])


def parse_datetime(value):
    """Returns an aware datetime in local timezone"""
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z").astimezone()


class Status:
    """
    A wrapper around the Status entity data fetched from Mastodon.

    https://github.com/tootsuite/documentation/blob/master/Using-the-API/API.md#status
    """
    def __init__(self, data, instance):
        self.data = data
        self.instance = instance

        self.id = self.data["id"]
        self.display_name = self.data["account"]["display_name"]
        self.account = self.get_account()
        self.created_at = parse_datetime(data["created_at"])
        self.author = get_author(data, instance)

        self.favourited = data.get("favourited", False)
        self.reblogged = data.get("reblogged", False)

    def get_account(self):
        acct = self.data['account']['acct']
        return acct if "@" in acct else "{}@{}".format(acct, self.instance)
