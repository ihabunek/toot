import inspect
import json
import typing

from datetime import date, datetime
from typing import List, Optional
from typing import get_origin, get_args
from functools import cache

from toot.utils import get_text


@cache
def get_type_hints_cached(cls):
    return typing.get_type_hints(cls)


def prune_optional(hint):
    if get_origin(hint) == typing.Union:
        args = get_args(hint)
        if len(args) == 2 and args[1] == type(None):
            return args[0]

    return hint


class Entity:
    def __init__(self, json_data: str):
        self._json = json_data
        self._data = json.loads(json_data)

    def __getattr__(self, name):
        hints = get_type_hints_cached(self.__class__)
        if name not in hints:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

        # TODO: read default value from field definition somehow
        default = None
        value = self._data.get(name, default)
        hint = prune_optional(hints[name])
        return self.convert(value, hint)

    def __repr__(self):
        def _fields():
            hints = get_type_hints_cached(self.__class__)
            for name, hint in hints.items():
                hint = prune_optional(hints[name])
                value = self._data.get(name)
                if value is None:
                    yield f"{name}=None"
                elif hint in [str, date, datetime]:
                    yield f"{name}='{value}'"
                elif hint in [int, bool, dict]:
                    yield f"{name}={value}"
                else:
                    yield f"{name}=..."

        name = self.__class__.__name__
        fields = ", ".join(_fields())
        return f"{name}({fields})"

    @property
    def __dict__(self):
        return self._data

    # TODO: override __dict__?
    # TODO: make readonly

    # def __setattribute__(self, name):
    #     raise Exception("Entities are read-only")

    # def __delattribute__(self, name):
    #     raise Exception("Entities are read-only")

    def convert(self, value, hint):
        if hint in [str, int, bool, dict]:
            return value

        if hint == datetime:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")

        if hint == date:
            return date.fromisoformat(value)

        if get_origin(hint) == list:
            (inner_hint,) = get_args(hint)
            return [self.convert(v, inner_hint) for v in value]

        if inspect.isclass(hint) and issubclass(hint, Entity):
            return hint(value)

        raise ValueError(f"hint??? {hint}")


class AccountField(Entity):
    """
    https://docs.joinmastodon.org/entities/Account/#Field
    """
    name: str
    value: str
    verified_at: Optional[datetime]


class CustomEmoji(Entity):
    """
    https://docs.joinmastodon.org/entities/CustomEmoji/
    """
    shortcode: str
    url: str
    static_url: str
    visible_in_picker: bool
    category: str


class Account(Entity):
    """
    https://docs.joinmastodon.org/entities/Account/
    """
    id: str
    username: str
    acct: str
    url: str
    display_name: str
    note: str
    avatar: str
    avatar_static: str
    header: str
    header_static: str
    locked: bool
    fields: List[AccountField]
    emojis: List[CustomEmoji]
    bot: bool
    group: bool
    discoverable: Optional[bool]
    noindex: Optional[bool]
    moved: Optional["Account"]
    suspended: bool = False
    limited: bool = False
    created_at: datetime
    last_status_at: Optional[date]
    statuses_count: int
    followers_count: int
    following_count: int

    @property
    def note_plaintext(self) -> str:
        return get_text(self.note)


class Application(Entity):
    name: str
    website: str


class MediaAttachment(Entity):
    id: str
    type: str
    url: str
    preview_url: str
    remote_url: Optional[str]
    meta: dict
    description: str
    blurhash: str


class StatusMention(Entity):
    """
    https://docs.joinmastodon.org/entities/Status/#Mention
    """
    id: str
    username: str
    url: str
    acct: str


class StatusTag(Entity):
    """
    https://docs.joinmastodon.org/entities/Status/#Tag
    """
    name: str
    url: str


class PollOption(Entity):
    """
    https://docs.joinmastodon.org/entities/Poll/#Option
    """
    title: str
    votes_count: Optional[int]


class Poll(Entity):
    """
    https://docs.joinmastodon.org/entities/Poll/
    """
    id: str
    expires_at: Optional[datetime]
    expired: bool
    multiple: bool
    votes_count: int
    voters_count: Optional[int]
    options: List[PollOption]
    emojis: List[CustomEmoji]
    voted: Optional[bool]
    own_votes: Optional[List[int]]


class PreviewCard(Entity):
    url: str
    title: str
    description: str
    type: str
    author_name: str
    author_url: str
    provider_name: str
    provider_url: str
    html: str
    width: int
    height: int
    image: Optional[str]
    embed_url: str
    blurhash: Optional[str]


class FilterKeyword(Entity):
    id: str
    keyword: str
    whole_word: str


class FilterStatus(Entity):
    id: str
    status_id: str


class Filter(Entity):
    id: str
    title: str
    context: List[str]
    expires_at: Optional[datetime]
    filter_action: str
    keywords: List[FilterKeyword]
    statuses: List[FilterStatus]


class FilterResult(Entity):
    filter: Filter
    keyword_matches: Optional[List[str]]
    status_matches: Optional[str]


class Status(Entity):
    id: str
    uri: str
    created_at: datetime
    account: Account
    content: str
    visibility: str
    sensitive: bool
    spoiler_text: str
    media_attachments: List[MediaAttachment]
    application: Optional[Application]
    mentions: List[StatusMention]
    tags: List[StatusTag]
    emojis: List[CustomEmoji]
    reblogs_count: int
    favourites_count: int
    replies_count: int
    url: Optional[str]
    in_reply_to_id: Optional[str]
    in_reply_to_account_id: Optional[str]
    reblog: Optional["Status"]
    poll: Optional[Poll]
    card: Optional[PreviewCard]
    language: Optional[str]
    text: Optional[str]
    edited_at: Optional[datetime]
    favourited: bool = False
    reblogged: bool = False
    muted: bool = False
    bookmarked: bool = False
    pinned: bool = False
    filtered: List[FilterResult]

    @property
    def original(self):
        return self.reblog or self
