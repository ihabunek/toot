"""
Dataclasses which represent entities returned by the Mastodon API.
"""

import dataclasses

from dataclasses import dataclass, is_dataclass
from datetime import date, datetime
from typing import Dict, List, Optional, Type, TypeVar, Union
from typing import get_type_hints

from toot.typing_compat import get_args, get_origin
from toot.utils import get_text


@dataclass
class AccountField:
    """
    https://docs.joinmastodon.org/entities/Account/#Field
    """
    name: str
    value: str
    verified_at: Optional[datetime]


@dataclass
class CustomEmoji:
    """
    https://docs.joinmastodon.org/entities/CustomEmoji/
    """
    shortcode: str
    url: str
    static_url: str
    visible_in_picker: bool
    category: str


@dataclass
class Account:
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
    suspended: Optional[bool]
    limited: Optional[bool]
    created_at: datetime
    last_status_at: Optional[date]
    statuses_count: int
    followers_count: int
    following_count: int

    @property
    def note_plaintext(self) -> str:
        return get_text(self.note)


@dataclass
class Application:
    """
    https://docs.joinmastodon.org/entities/Status/#application
    """
    name: str
    website: Optional[str]


@dataclass
class MediaAttachment:
    """
    https://docs.joinmastodon.org/entities/MediaAttachment/
    """
    id: str
    type: str
    url: str
    preview_url: str
    remote_url: Optional[str]
    meta: dict
    description: str
    blurhash: str


@dataclass
class StatusMention:
    """
    https://docs.joinmastodon.org/entities/Status/#Mention
    """
    id: str
    username: str
    url: str
    acct: str


@dataclass
class StatusTag:
    """
    https://docs.joinmastodon.org/entities/Status/#Tag
    """
    name: str
    url: str


@dataclass
class PollOption:
    """
    https://docs.joinmastodon.org/entities/Poll/#Option
    """
    title: str
    votes_count: Optional[int]


@dataclass
class Poll:
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


@dataclass
class PreviewCard:
    """
    https://docs.joinmastodon.org/entities/PreviewCard/
    """
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


@dataclass
class FilterKeyword:
    """
    https://docs.joinmastodon.org/entities/FilterKeyword/
    """
    id: str
    keyword: str
    whole_word: str


@dataclass
class FilterStatus:
    """
    https://docs.joinmastodon.org/entities/FilterStatus/
    """
    id: str
    status_id: str


@dataclass
class Filter:
    """
    https://docs.joinmastodon.org/entities/Filter/
    """
    id: str
    title: str
    context: List[str]
    expires_at: Optional[datetime]
    filter_action: str
    keywords: List[FilterKeyword]
    statuses: List[FilterStatus]


@dataclass
class FilterResult:
    """
    https://docs.joinmastodon.org/entities/FilterResult/
    """
    filter: Filter
    keyword_matches: Optional[List[str]]
    status_matches: Optional[str]


@dataclass
class Status:
    """
    https://docs.joinmastodon.org/entities/Status/
    """
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
    favourited: Optional[bool]
    reblogged: Optional[bool]
    muted: Optional[bool]
    bookmarked: Optional[bool]
    pinned: Optional[bool]
    filtered: Optional[List[FilterResult]]

    @property
    def original(self) -> "Status":
        return self.reblog or self


@dataclass
class Report:
    """
    https://docs.joinmastodon.org/entities/Report/
    """
    id: str
    action_taken: bool
    action_taken_at: Optional[datetime]
    category: str
    comment: str
    forwarded: bool
    created_at: datetime
    status_ids: Optional[List[str]]
    rule_ids: Optional[List[str]]
    target_account: Account


@dataclass
class Notification:
    """
    https://docs.joinmastodon.org/entities/Notification/
    """
    id: str
    type: str
    created_at: datetime
    account: Account
    status: Optional[Status]
    report: Optional[Report]


@dataclass
class InstanceUrls:
    streaming_api: str


@dataclass
class InstanceStats:
    user_count: int
    status_count: int
    domain_count: int


@dataclass
class InstanceConfigurationStatuses:
    max_characters: int
    max_media_attachments: int
    characters_reserved_per_url: int


@dataclass
class InstanceConfigurationMediaAttachments:
    supported_mime_types: List[str]
    image_size_limit: int
    image_matrix_limit: int
    video_size_limit: int
    video_frame_rate_limit: int
    video_matrix_limit: int


@dataclass
class InstanceConfigurationPolls:
    max_options: int
    max_characters_per_option: int
    min_expiration: int
    max_expiration: int


@dataclass
class InstanceConfiguration:
    """
    https://docs.joinmastodon.org/entities/V1_Instance/#configuration
    """
    statuses: InstanceConfigurationStatuses
    media_attachments: InstanceConfigurationMediaAttachments
    polls: InstanceConfigurationPolls


@dataclass
class Rule:
    """
    https://docs.joinmastodon.org/entities/Rule/
    """
    id: str
    text: str


@dataclass
class Instance:
    """
    https://docs.joinmastodon.org/entities/V1_Instance/
    """
    uri: str
    title: str
    short_description: str
    description: str
    email: str
    version: str
    urls: InstanceUrls
    stats: InstanceStats
    thumbnail: Optional[str]
    languages: List[str]
    registrations: bool
    approval_required: bool
    invites_enabled: bool
    configuration: InstanceConfiguration
    contact_account: Optional[Account]
    rules: List[Rule]


# Generic data class instance
T = TypeVar("T")


def from_dict(cls: Type[T], data: Dict) -> T:
    """Convert a nested dict into an instance of `cls`."""
    def _fields():
        hints = get_type_hints(cls)
        for field in dataclasses.fields(cls):
            field_type = _prune_optional(hints[field.name])
            default_value = _get_default_value(field)
            value = data.get(field.name, default_value)
            yield field.name, _convert(field_type, value)

    return cls(**dict(_fields()))


def _get_default_value(field):
    if field.default is not dataclasses.MISSING:
        return field.default

    if field.default_factory is not dataclasses.MISSING:
        return field.default_factory()

    return None


def _convert(field_type, value):
    if value is None:
        return None

    if field_type in [str, int, bool, dict]:
        return value

    if field_type == datetime:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")

    if field_type == date:
        return date.fromisoformat(value)

    if get_origin(field_type) == list:
        (inner_type,) = get_args(field_type)
        return [_convert(inner_type, x) for x in value]

    if is_dataclass(field_type):
        return from_dict(field_type, value)

    raise ValueError(f"Not implemented for type '{field_type}'")


def _prune_optional(field_type):
    """For `Optional[<type>]` returns the encapsulated `<type>`."""
    if get_origin(field_type) == Union:
        args = get_args(field_type)
        if len(args) == 2 and args[1] == type(None):  # noqa
            return args[0]

    return field_type
