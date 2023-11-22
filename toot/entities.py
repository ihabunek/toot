"""
Dataclasses which represent entities returned by the Mastodon API.

Data classes my have an optional static method named `__toot_prepare__` which is
used when constructing the data class using `from_dict`. The method will be
called with the dict and may modify it and return a modified dict. This is used
to implement any pre-processing which may be required, e.g. to support
different versions of the Mastodon API.
"""

import dataclasses

from dataclasses import dataclass, is_dataclass
from datetime import date, datetime
from typing import Dict, List, Optional, Type, TypeVar, Union
from typing import get_type_hints

from toot.typing_compat import get_args, get_origin
from toot.utils import get_text
from toot.utils.datetime import parse_datetime


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
    source: Optional[dict]

    @staticmethod
    def __toot_prepare__(obj: Dict) -> Dict:
        # Pleroma has not yet converted last_status_at from datetime to date
        # so trim it here so it doesn't break when converting to date.
        # See: https://git.pleroma.social/pleroma/pleroma/-/issues/1470
        last_status_at = obj.get("last_status_at")
        if last_status_at:
            obj.update(last_status_at=obj["last_status_at"][:10])
        return obj

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

    @staticmethod
    def __toot_prepare__(obj: Dict) -> Dict:
        # Pleroma has a bug where created_at is set to an empty string.
        # To avoid marking created_at as optional, which would require work
        # because we count on it always existing, set it to current datetime.
        # Possible underlying issue:
        # https://git.pleroma.social/pleroma/pleroma/-/issues/2851
        if not obj["created_at"]:
            obj["created_at"] = datetime.now().astimezone().isoformat()
        return obj


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


@dataclass
class Relationship:
    """
    Represents the relationship between accounts, such as following / blocking /
    muting / etc.
    https://docs.joinmastodon.org/entities/Relationship/
    """
    id: str
    following: bool
    showing_reblogs: bool
    notifying: bool
    languages: List[str]
    followed_by: bool
    blocking: bool
    blocked_by: bool
    muting: bool
    muting_notifications: bool
    requested: bool
    domain_blocking: bool
    endorsed: bool
    note: str


# Generic data class instance
T = TypeVar("T")


class ConversionError(Exception):
    """Raised when conversion fails from JSON value to data class field."""
    def __init__(
        self,
        data_class: Type,
        field_name: str,
        field_type: Type,
        field_value: Optional[str]
    ):
        super().__init__(
            f"Failed converting field `{data_class.__name__}.{field_name}` "
            + f"of type `{field_type.__name__}` from value {field_value!r}"
        )


def from_dict(cls: Type[T], data: Dict) -> T:
    """Convert a nested dict into an instance of `cls`."""
    # Apply __toot_prepare__ if it exists
    prepare = getattr(cls, '__toot_prepare__', None)
    if prepare:
        data = prepare(data)

    def _fields():
        hints = get_type_hints(cls)
        for field in dataclasses.fields(cls):
            field_type = _prune_optional(hints[field.name])
            default_value = _get_default_value(field)
            value = data.get(field.name, default_value)
            converted = _convert_with_error_handling(cls, field.name, field_type, value)
            yield field.name, converted

    return cls(**dict(_fields()))


def from_dict_list(cls: Type[T], data: List[Dict]) -> List[T]:
    return [from_dict(cls, x) for x in data]


def _get_default_value(field):
    if field.default is not dataclasses.MISSING:
        return field.default

    if field.default_factory is not dataclasses.MISSING:
        return field.default_factory()

    return None


def _convert_with_error_handling(
    data_class: Type,
    field_name: str,
    field_type: Type,
    field_value: Optional[str]
):
    try:
        return _convert(field_type, field_value)
    except ConversionError:
        raise
    except Exception:
        raise ConversionError(data_class, field_name, field_type, field_value)


def _convert(field_type, value):
    if value is None:
        return None

    if field_type in [str, int, bool, dict]:
        return value

    if field_type == datetime:
        return parse_datetime(value)

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
