from collections import namedtuple

from toot.utils.datetime import parse_datetime

Author = namedtuple("Author", ["account", "display_name", "username"])


class Status:
    """
    A wrapper around the Status entity data fetched from Mastodon.

    https://github.com/tootsuite/documentation/blob/master/Using-the-API/API.md#status

    Attributes
    ----------
    reblog : Status or None
        The reblogged status if it exists.

    original : Status
        If a reblog, the reblogged status, otherwise self.
    """

    def __init__(self, data, is_mine, default_instance):
        """
        Parameters
        ----------
        data : dict
            Status data as received from Mastodon.
            https://docs.joinmastodon.org/api/entities/#status

        is_mine : bool
            Whether the status was created by the logged in user.

        default_instance : str
            The domain of the instance into which the user is logged in. Used to
            create fully qualified account names for users on the same instance.
            Mastodon only populates the name, not the domain.
        """

        self.data = data
        self.is_mine = is_mine
        self.default_instance = default_instance

        # This can be toggled by the user
        self.show_sensitive = False

        # Set when status is translated
        self.show_translation = False
        self.translation = None
        self.translated_from = None

        # TODO: clean up
        self.id = self.data["id"]
        self.account = self._get_account()
        self.created_at = parse_datetime(data["created_at"])
        self.author = self._get_author()
        self.favourited = data.get("favourited", False)
        self.reblogged = data.get("reblogged", False)
        self.bookmarked = data.get("bookmarked", False)
        self.in_reply_to = data.get("in_reply_to_id")
        self.url = data.get("url")
        self.mentions = data.get("mentions")
        self.reblog = self._get_reblog()
        self.visibility = data.get("visibility")

    @property
    def original(self):
        return self.reblog or self

    def _get_reblog(self):
        reblog = self.data.get("reblog")
        if not reblog:
            return None

        reblog_is_mine = self.is_mine and (
            self.data["account"]["acct"] == reblog["account"]["acct"]
        )
        return Status(reblog, reblog_is_mine, self.default_instance)

    def _get_author(self):
        acct = self.data['account']['acct']
        acct = acct if "@" in acct else "{}@{}".format(acct, self.default_instance)
        return Author(acct, self.data['account']['display_name'], self.data['account']['username'])

    def _get_account(self):
        acct = self.data['account']['acct']
        return acct if "@" in acct else "{}@{}".format(acct, self.default_instance)

    def __repr__(self):
        return "<Status id={} account={}>".format(self.id, self.account)
