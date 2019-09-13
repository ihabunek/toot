from collections import namedtuple

from .utils import parse_datetime


Author = namedtuple("Author", ["account", "display_name"])


class Status:
    """
    A wrapper around the Status entity data fetched from Mastodon.

    https://github.com/tootsuite/documentation/blob/master/Using-the-API/API.md#status
    """
    def __init__(self, data, is_mine, default_instance):
        self.data = data
        self.is_mine = is_mine
        self.default_instance = default_instance

        # This can be toggled by the user
        self.show_sensitive = False

        # TODO: make Status immutable?

        self.id = self.data["id"]
        self.display_name = self.data["account"]["display_name"]
        self.account = self.get_account()
        self.created_at = parse_datetime(data["created_at"])
        self.author = self.get_author()
        self.favourited = data.get("favourited", False)
        self.reblogged = data.get("reblogged", False)
        self.in_reply_to = data.get("in_reply_to_id")

        self.reblog = reblog = data.get("reblog")
        self.url = reblog.get("url") if reblog else data.get("url")

        self.mentions = data["mentions"]

    def get_author(self):
        # Show the author, not the persopn who reblogged
        data = self.data["reblog"] or self.data
        acct = data['account']['acct']
        acct = acct if "@" in acct else "{}@{}".format(acct, self.default_instance)
        return Author(acct, data['account']['display_name'])

    def get_account(self):
        reblog = self.data.get("reblog")
        account = reblog['account'] if reblog else self.data['account']
        acct = account['acct']
        return acct if "@" in acct else "{}@{}".format(acct, self.default_instance)

    def __repr__(self):
        return "<Status id={}>".format(self.id)
