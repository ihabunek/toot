import logging
import os
import re
import shutil
import sys

from argparse import ArgumentParser, FileType, ArgumentTypeError, Action
from collections import namedtuple
from itertools import chain
from toot import config, commands, CLIENT_NAME, CLIENT_WEBSITE, __version__, settings
from toot.exceptions import ApiError, ConsoleError
from toot.output import print_out, print_err
from toot.settings import get_setting

VISIBILITY_CHOICES = ["public", "unlisted", "private", "direct"]
VISIBILITY_CHOICES_STR = ", ".join(f"'{v}'" for v in VISIBILITY_CHOICES)

PRIVACY_CHOICES = ["public", "unlisted", "private"]
PRIVACY_CHOICES_STR = ", ".join(f"'{v}'" for v in PRIVACY_CHOICES)


class BooleanOptionalAction(Action):
    """
    Backported from argparse. This action is available since Python 3.9.
    https://github.com/python/cpython/blob/3.11/Lib/argparse.py
    """
    def __init__(self,
                 option_strings,
                 dest,
                 default=None,
                 type=None,
                 choices=None,
                 required=False,
                 help=None,
                 metavar=None):

        _option_strings = []
        for option_string in option_strings:
            _option_strings.append(option_string)

            if option_string.startswith('--'):
                option_string = '--no-' + option_string[2:]
                _option_strings.append(option_string)

        super().__init__(
            option_strings=_option_strings,
            dest=dest,
            nargs=0,
            default=default,
            type=type,
            choices=choices,
            required=required,
            help=help,
            metavar=metavar)

    def __call__(self, parser, namespace, values, option_string=None):
        if option_string in self.option_strings:
            setattr(namespace, self.dest, not option_string.startswith('--no-'))

    def format_usage(self):
        return ' | '.join(self.option_strings)


def get_default_visibility():
    return os.getenv("TOOT_POST_VISIBILITY", "public")


def language(value):
    """Validates the language parameter"""
    if len(value) != 2:
        raise ArgumentTypeError(
            "Invalid language. Expected a 2 letter abbreviation according to "
            "the ISO 639-1 standard."
        )

    return value


def visibility(value):
    """Validates the visibility parameter"""
    if value not in VISIBILITY_CHOICES:
        raise ValueError("Invalid visibility value")

    return value


def privacy(value):
    """Validates the privacy parameter"""
    if value not in PRIVACY_CHOICES:
        raise ValueError(f"Invalid privacy value. Expected one of {PRIVACY_CHOICES_STR}.")

    return value


def timeline_count(value):
    n = int(value)
    if not 0 < n <= 20:
        raise ArgumentTypeError("Number of toots should be between 1 and 20.")
    return n


DURATION_UNITS = {
    "m": 60,
    "h": 60 * 60,
    "d": 60 * 60 * 24,
}


DURATION_EXAMPLES = """e.g. "1 day", "2 hours 30 minutes", "5 minutes 30
seconds" or any combination of above. Shorthand: "1d", "2h30m", "5m30s\""""


def duration(value: str):
    match = re.match(r"""^
        (([0-9]+)\s*(days|day|d))?\s*
        (([0-9]+)\s*(hours|hour|h))?\s*
        (([0-9]+)\s*(minutes|minute|m))?\s*
        (([0-9]+)\s*(seconds|second|s))?\s*
    $""", value, re.X)

    if not match:
        raise ArgumentTypeError(f"Invalid duration: {value}")

    days = match.group(2)
    hours = match.group(5)
    minutes = match.group(8)
    seconds = match.group(11)

    days = int(match.group(2) or 0) * 60 * 60 * 24
    hours = int(match.group(5) or 0) * 60 * 60
    minutes = int(match.group(8) or 0) * 60
    seconds = int(match.group(11) or 0)

    duration = days + hours + minutes + seconds

    if duration == 0:
        raise ArgumentTypeError("Empty duration")

    return duration


def editor(value):
    if not value:
        raise ArgumentTypeError(
            "Editor not specified in --editor option and $EDITOR environment "
            "variable not set."
        )

    # Check editor executable exists
    exe = shutil.which(value)
    if not exe:
        raise ArgumentTypeError("Editor `{}` not found".format(value))

    return exe


Command = namedtuple("Command", ["name", "description", "require_auth", "arguments"])


# Arguments added to every command
common_args = [
    (["--no-color"], {
        "help": "don't use ANSI colors in output",
        "action": 'store_true',
        "default": False,
    }),
    (["--quiet"], {
        "help": "don't write to stdout on success",
        "action": 'store_true',
        "default": False,
    }),
    (["--debug"], {
        "help": "show debug log in console",
        "action": 'store_true',
        "default": False,
    }),
    (["--verbose"], {
        "help": "show extra detail in debug log; used with --debug",
        "action": 'store_true',
        "default": False,
    }),
]

# Arguments added to commands which require authentication
common_auth_args = [
    (["-u", "--using"], {
        "help": "the account to use, overrides active account",
    }),
]

account_arg = (["account"], {
    "help": "account name, e.g. 'Gargron@mastodon.social'",
})

optional_account_arg = (["account"], {
    "nargs": "?",
    "help": "account name, e.g. 'Gargron@mastodon.social'",
})

instance_arg = (["-i", "--instance"], {
    "type": str,
    "help": 'mastodon instance to log into e.g. "mastodon.social"',
})

email_arg = (["-e", "--email"], {
    "type": str,
    "help": 'email address to log in with',
})

scheme_arg = (["--disable-https"], {
    "help": "disable HTTPS and use insecure HTTP",
    "dest": "scheme",
    "default": "https",
    "action": "store_const",
    "const": "http",
})

status_id_arg = (["status_id"], {
    "help": "ID of the status",
    "type": str,
})

visibility_arg = (["-v", "--visibility"], {
    "type": visibility,
    "default": get_default_visibility(),
    "help": f"Post visibility. One of: {VISIBILITY_CHOICES_STR}. Defaults to "
            f"'{get_default_visibility()}' which can be overridden by setting "
            "the TOOT_POST_VISIBILITY environment variable",
})

tag_arg = (["tag_name"], {
    "type": str,
    "help": "tag name, e.g. Caturday, or \"#Caturday\"",
})

json_arg = (["--json"], {
    "action": "store_true",
    "default": False,
    "help": "print json instead of plaintext",
})

# Arguments for selecting a timeline (see `toot.commands.get_timeline_generator`)
common_timeline_args = [
    (["-p", "--public"], {
        "action": "store_true",
        "default": False,
        "help": "show public timeline (does not require auth)",
    }),
    (["-t", "--tag"], {
        "type": str,
        "help": "show hashtag timeline (does not require auth)",
    }),
    (["-a", "--account"], {
        "type": str,
        "help": "show timeline for the given account",
    }),
    (["-l", "--local"], {
        "action": "store_true",
        "default": False,
        "help": "show only statuses from local instance (public and tag timelines only)",
    }),
    (["-i", "--instance"], {
        "type": str,
        "help": "mastodon instance from which to read (public and tag timelines only)",
    }),
    (["--list"], {
        "type": str,
        "help": "show timeline for given list.",
    }),
]

timeline_and_bookmark_args = [
    (["-c", "--count"], {
        "type": timeline_count,
        "help": "number of toots to show per page (1-20, default 10).",
        "default": 10,
    }),
    (["-r", "--reverse"], {
        "action": "store_true",
        "default": False,
        "help": "Reverse the order of the shown timeline (to new posts at the bottom)",
    }),
    (["-1", "--once"], {
        "action": "store_true",
        "default": False,
        "help": "Only show the first <count> toots, do not prompt to continue.",
    }),
]

timeline_args = common_timeline_args + timeline_and_bookmark_args

AUTH_COMMANDS = [
    Command(
        name="login",
        description="Log into a mastodon instance using your browser (recommended)",
        arguments=[instance_arg, scheme_arg],
        require_auth=False,
    ),
    Command(
        name="login_cli",
        description="Log in from the console, does NOT support two factor authentication",
        arguments=[instance_arg, email_arg, scheme_arg],
        require_auth=False,
    ),
    Command(
        name="activate",
        description="Switch between logged in accounts.",
        arguments=[optional_account_arg],
        require_auth=False,
    ),
    Command(
        name="logout",
        description="Log out, delete stored access keys",
        arguments=[account_arg],
        require_auth=False,
    ),
    Command(
        name="auth",
        description="Show logged in accounts and instances",
        arguments=[],
        require_auth=False,
    ),
    Command(
        name="env",
        description="Print environment information for inclusion in bug reports.",
        arguments=[],
        require_auth=False,
    ),
    Command(
        name="update_account",
        description="Update your account details",
        arguments=[
            (["--display-name"], {
                "type": str,
                "help": "The display name to use for the profile.",
            }),
            (["--note"], {
                "type": str,
                "help": "The account bio.",
            }),
            (["--avatar"], {
                "type": FileType("rb"),
                "help": "Path to the avatar image to set.",
            }),
            (["--header"], {
                "type": FileType("rb"),
                "help": "Path to the header image to set.",
            }),
            (["--bot"], {
                "action": BooleanOptionalAction,
                "help": "Whether the account has a bot flag.",
            }),
            (["--discoverable"], {
                "action": BooleanOptionalAction,
                "help": "Whether the account should be shown in the profile directory.",
            }),
            (["--locked"], {
                "action": BooleanOptionalAction,
                "help": "Whether manual approval of follow requests is required.",
            }),
            (["--privacy"], {
                "type": privacy,
                "help": f"Default post privacy for authored statuses. One of: {PRIVACY_CHOICES_STR}."
            }),
            (["--sensitive"], {
                "action": BooleanOptionalAction,
                "help": "Whether to mark authored statuses as sensitive by default."
            }),
            (["--language"], {
                "type": language,
                "help": "Default language to use for authored statuses (ISO 639-1)."
            }),
            json_arg,
        ],
        require_auth=True,
    ),
]

TUI_COMMANDS = [
    Command(
        name="tui",
        description="Launches the toot terminal user interface",
        arguments=[
            (["--relative-datetimes"], {
                "action": "store_true",
                "default": False,
                "help": "Show relative datetimes in status list.",
            }),
        ],
        require_auth=True,
    ),
]


READ_COMMANDS = [
    Command(
        name="whoami",
        description="Display logged in user details",
        arguments=[json_arg],
        require_auth=True,
    ),
    Command(
        name="whois",
        description="Display account details",
        arguments=[
            (["account"], {
                "help": "account name or numeric ID"
            }),
            json_arg,
        ],
        require_auth=True,
    ),
    Command(
        name="notifications",
        description="Notifications for logged in user",
        arguments=[
            (["--clear"], {
                "help": "delete all notifications from the server",
                "action": 'store_true',
                "default": False,
            }),
            (["-r", "--reverse"], {
                "action": "store_true",
                "default": False,
                "help": "Reverse the order of the shown notifications (newest on top)",
            }),
            (["-m", "--mentions"], {
                "action": "store_true",
                "default": False,
                "help": "Only print mentions",
            })
        ],
        require_auth=True,
    ),
    Command(
        name="instance",
        description="Display instance details",
        arguments=[
            (["instance"], {
                "help": "instance domain (e.g. 'mastodon.social') or blank to use current",
                "nargs": "?",
            }),
            scheme_arg,
            json_arg,
        ],
        require_auth=False,
    ),
    Command(
        name="search",
        description="Search for users or hashtags",
        arguments=[
            (["query"], {
                "help": "the search query",
            }),
            (["-r", "--resolve"], {
                "action": 'store_true',
                "default": False,
                "help": "Resolve non-local accounts",
            }),
            json_arg,
        ],
        require_auth=True,
    ),
    Command(
        name="thread",
        description="Show toot thread items",
        arguments=[
            (["status_id"], {
                "help": "Show thread for toot.",
            }),
            json_arg,
        ],
        require_auth=True,
    ),
    Command(
        name="status",
        description="Show a single status",
        arguments=[
            (["status_id"], {
                "help": "ID of the status to show.",
            }),
            json_arg,
        ],
        require_auth=True,
    ),
    Command(
        name="timeline",
        description="Show recent items in a timeline (home by default)",
        arguments=timeline_args,
        require_auth=True,
    ),
    Command(
        name="bookmarks",
        description="Show bookmarked posts",
        arguments=timeline_and_bookmark_args,
        require_auth=True,
    ),
]

POST_COMMANDS = [
    Command(
        name="post",
        description="Post a status text to your timeline",
        arguments=[
            (["text"], {
                "help": "The status text to post.",
                "nargs": "?",
            }),
            (["-m", "--media"], {
                "action": "append",
                "type": FileType("rb"),
                "help": "path to the media file to attach (specify multiple "
                        "times to attach up to 4 files)"
            }),
            (["-d", "--description"], {
                "action": "append",
                "type": str,
                "help": "plain-text description of the media for accessibility "
                        "purposes, one per attached media"
            }),
            (["--thumbnail"], {
                "action": "append",
                "type": FileType("rb"),
                "help": "path to an image file to serve as media thumbnail, "
                        "one per attached media"
            }),
            visibility_arg,
            (["-s", "--sensitive"], {
                "action": 'store_true',
                "default": False,
                "help": "mark the media as NSFW",
            }),
            (["-p", "--spoiler-text"], {
                "type": str,
                "help": "text to be shown as a warning before the actual content",
            }),
            (["-r", "--reply-to"], {
                "type": str,
                "help": "local ID of the status you want to reply to",
            }),
            (["-l", "--language"], {
                "type": language,
                "help": "ISO 639-1 language code of the toot, to skip automatic detection",
            }),
            (["-e", "--editor"], {
                "type": editor,
                "nargs": "?",
                "const": os.getenv("EDITOR", ""),  # option given without value
                "help": "Specify an editor to compose your toot, "
                        "defaults to editor defined in $EDITOR env variable.",
            }),
            (["--scheduled-at"], {
                "type": str,
                "help": "ISO 8601 Datetime at which to schedule a status. Must "
                        "be at least 5 minutes in the future.",
            }),
            (["--scheduled-in"], {
                "type": duration,
                "help": f"""Schedule the toot to be posted after a given amount
                        of time, {DURATION_EXAMPLES}. Must be at least 5
                        minutes.""",
            }),
            (["-t", "--content-type"], {
                "type": str,
                "help": "MIME type for the status text (not supported on all instances)",
            }),
            (["--poll-option"], {
                "action": "append",
                "type": str,
                "help": "Possible answer to the poll"
            }),
            (["--poll-expires-in"], {
                "type": duration,
                "help": f"""Duration that the poll should be open,
                        {DURATION_EXAMPLES}. Defaults to 24h.""",
                "default": 24 * 60 * 60,
            }),
            (["--poll-multiple"], {
                "action": "store_true",
                "default": False,
                "help": "Allow multiple answers to be selected."
            }),
            (["--poll-hide-totals"], {
                "action": "store_true",
                "default": False,
                "help": "Hide vote counts until the poll ends. Defaults to false."
            }),
            json_arg,
        ],
        require_auth=True,
    ),
    Command(
        name="upload",
        description="Upload an image or video file",
        arguments=[
            (["file"], {
                "help": "Path to the file to upload",
                "type": FileType('rb')
            }),
            (["-d", "--description"], {
                "type": str,
                "help": "plain-text description of the media for accessibility purposes"
            }),
        ],
        require_auth=True,
    ),
]

STATUS_COMMANDS = [
    Command(
        name="delete",
        description="Delete a status",
        arguments=[status_id_arg, json_arg],
        require_auth=True,
    ),
    Command(
        name="favourite",
        description="Favourite a status",
        arguments=[status_id_arg, json_arg],
        require_auth=True,
    ),
    Command(
        name="unfavourite",
        description="Unfavourite a status",
        arguments=[status_id_arg, json_arg],
        require_auth=True,
    ),
    Command(
        name="reblog",
        description="Reblog a status",
        arguments=[status_id_arg, visibility_arg, json_arg],
        require_auth=True,
    ),
    Command(
        name="unreblog",
        description="Unreblog a status",
        arguments=[status_id_arg, json_arg],
        require_auth=True,
    ),
    Command(
        name="reblogged_by",
        description="Show accounts that reblogged the status",
        arguments=[status_id_arg, json_arg],
        require_auth=False,
    ),
    Command(
        name="pin",
        description="Pin a status",
        arguments=[status_id_arg, json_arg],
        require_auth=True,
    ),
    Command(
        name="unpin",
        description="Unpin a status",
        arguments=[status_id_arg, json_arg],
        require_auth=True,
    ),
    Command(
        name="bookmark",
        description="Bookmark a status",
        arguments=[status_id_arg, json_arg],
        require_auth=True,
    ),
    Command(
        name="unbookmark",
        description="Unbookmark a status",
        arguments=[status_id_arg, json_arg],
        require_auth=True,
    ),
]

ACCOUNTS_COMMANDS = [
    Command(
        name="follow",
        description="Follow an account",
        arguments=[account_arg, json_arg],
        require_auth=True,
    ),
    Command(
        name="unfollow",
        description="Unfollow an account",
        arguments=[account_arg, json_arg],
        require_auth=True,
    ),
    Command(
        name="following",
        description="List accounts followed by the given account, " +
                    "or your account if no account given",
        arguments=[optional_account_arg, json_arg],
        require_auth=True,
    ),
    Command(
        name="followers",
        description="List accounts following the given account, " +
                    "or your account if no account given",
        arguments=[optional_account_arg, json_arg],
        require_auth=True,
    ),
    Command(
        name="mute",
        description="Mute an account",
        arguments=[account_arg, json_arg],
        require_auth=True,
    ),
    Command(
        name="unmute",
        description="Unmute an account",
        arguments=[account_arg, json_arg],
        require_auth=True,
    ),
    Command(
        name="muted",
        description="List muted accounts",
        arguments=[json_arg],
        require_auth=True,
    ),
    Command(
        name="block",
        description="Block an account",
        arguments=[account_arg, json_arg],
        require_auth=True,
    ),
    Command(
        name="unblock",
        description="Unblock an account",
        arguments=[account_arg, json_arg],
        require_auth=True,
    ),
    Command(
        name="blocked",
        description="List blocked accounts",
        arguments=[json_arg],
        require_auth=True,
    ),
]

TAG_COMMANDS = [
    Command(
        name="tags_followed",
        description="List hashtags you follow",
        arguments=[],
        require_auth=True,
    ),
    Command(
        name="tags_follow",
        description="Follow a hashtag",
        arguments=[tag_arg],
        require_auth=True,
    ),
    Command(
        name="tags_unfollow",
        description="Unfollow a hashtag",
        arguments=[tag_arg],
        require_auth=True,
    ),
]

LIST_COMMANDS = [
    Command(
        name="lists",
        description="List all lists",
        arguments=[],
        require_auth=True,
    ),
    Command(
        name="list_accounts",
        description="List the accounts in a list",
        arguments=[
            (["--id"], {
                "type": str,
                "help": "ID of the list"
            }),
            (["title"], {
                "type": str,
                "nargs": "?",
                "help": "title of the list"
            }),
        ],
        require_auth=True,
    ),
    Command(
        name="list_create",
        description="Create a list",
        arguments=[
            (["title"], {
                "type": str,
                "help": "title of the list"
            }),
            (["--replies-policy"], {
                "type": str,
                "help": "replies policy: 'followed', 'list', or 'none' (defaults to 'none')"
            }),
        ],
        require_auth=True,
    ),
    Command(
        name="list_delete",
        description="Delete a list",
        arguments=[
            (["--id"], {
                "type": str,
                "help": "ID of the list"
            }),
            (["title"], {
                "type": str,
                "nargs": "?",
                "help": "title of the list"
            }),
        ],
        require_auth=True,
    ),
    Command(
        name="list_add",
        description="Add account to list",
        arguments=[
            (["--id"], {
                "type": str,
                "help": "ID of the list"
            }),
            (["title"], {
                "type": str,
                "nargs": "?",
                "help": "title of the list"
            }),
            (["account"], {
                "type": str,
                "help": "Account to add"
            }),
        ],
        require_auth=True,
    ),
    Command(
        name="list_remove",
        description="Remove account from list",
        arguments=[
            (["--id"], {
                "type": str,
                "help": "ID of the list"
            }),
            (["title"], {
                "type": str,
                "nargs": "?",
                "help": "title of the list"
            }),
            (["account"], {
                "type": str,
                "help": "Account to remove"
            }),
        ],
        require_auth=True,
    ),
]
COMMAND_GROUPS = [
    ("Authentication", AUTH_COMMANDS),
    ("TUI", TUI_COMMANDS),
    ("Read", READ_COMMANDS),
    ("Post", POST_COMMANDS),
    ("Status", STATUS_COMMANDS),
    ("Accounts", ACCOUNTS_COMMANDS),
    ("Hashtags", TAG_COMMANDS),
    ("Lists", LIST_COMMANDS),
]

COMMANDS = list(chain(*[commands for _, commands in COMMAND_GROUPS]))


def print_usage():
    max_name_len = max(len(name) for name, _ in COMMAND_GROUPS)

    print_out("<green>{}</green>".format(CLIENT_NAME))
    print_out("<blue>v{}</blue>".format(__version__))

    for name, cmds in COMMAND_GROUPS:
        print_out("")
        print_out(name + ":")

        for cmd in cmds:
            cmd_name = cmd.name.ljust(max_name_len + 2)
            print_out("  <yellow>toot {}</yellow> {}".format(cmd_name, cmd.description))

    print_out("")
    print_out("To get help for each command run:")
    print_out("  <yellow>toot \\<command> --help</yellow>")
    print_out("")
    print_out("<green>{}</green>".format(CLIENT_WEBSITE))


def get_argument_parser(name, command):
    parser = ArgumentParser(
        prog='toot %s' % name,
        description=command.description,
        epilog=CLIENT_WEBSITE)

    combined_args = command.arguments + common_args
    if command.require_auth:
        combined_args += common_auth_args

    defaults = get_setting(f"commands.{name}", dict, {})

    for args, kwargs in combined_args:
        # Set default value from settings if exists
        default = get_default_value(defaults, args)
        if default is not None:
            kwargs["default"] = default
        parser.add_argument(*args, **kwargs)

    return parser


def get_default_value(defaults, args):
    # Hacky way to determine command name from argparse args
    name = args[-1].lstrip("-").replace("-", "_")
    return defaults.get(name)


def run_command(app, user, name, args):
    command = next((c for c in COMMANDS if c.name == name), None)

    if not command:
        print_err(f"Unknown command '{name}'")
        print_out("Run <yellow>toot --help</yellow> to show a list of available commands.")
        return

    parser = get_argument_parser(name, command)
    parsed_args = parser.parse_args(args)

    # Override the active account if 'using' option is given
    if command.require_auth and parsed_args.using:
        user, app = config.get_user_app(parsed_args.using)
        if not user or not app:
            raise ConsoleError("User '{}' not found".format(parsed_args.using))

    if command.require_auth and (not user or not app):
        print_err("This command requires that you are logged in.")
        print_err("Please run `toot login` first.")
        return

    fn = commands.__dict__.get(name)

    if not fn:
        raise NotImplementedError("Command '{}' does not have an implementation.".format(name))

    return fn(app, user, parsed_args)


def main():
    if settings.get_debug():
        filename = settings.get_debug_file()
        logging.basicConfig(level=logging.DEBUG, filename=filename)
        logging.getLogger("urllib3").setLevel(logging.INFO)

    command_name = sys.argv[1] if len(sys.argv) > 1 else None
    args = sys.argv[2:]

    if not command_name or command_name == "--help":
        return print_usage()

    user, app = config.get_active_user_app()

    try:
        run_command(app, user, command_name, args)
    except (ConsoleError, ApiError) as e:
        print_err(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        pass
