# -*- coding: utf-8 -*-

import logging
import os
import shutil
import sys

from argparse import ArgumentParser, FileType, ArgumentTypeError
from collections import namedtuple
from toot import config, commands, CLIENT_NAME, CLIENT_WEBSITE, __version__
from toot.exceptions import ApiError, ConsoleError
from toot.output import print_out, print_err

VISIBILITY_CHOICES = ['public', 'unlisted', 'private', 'direct']


def language(value):
    """Validates the language parameter"""
    if len(value) != 3:
        raise ArgumentTypeError(
            "Invalid language specified: '{}'. Expected a 3 letter "
            "abbreviation according to ISO 639-2 standard.".format(value)
        )

    return value


def visibility(value):
    """Validates the visibility parameter"""
    if value not in VISIBILITY_CHOICES:
        raise ValueError("Invalid visibility value")

    return value


def timeline_count(value):
    n = int(value)
    if not 0 < n <= 20:
        raise ArgumentTypeError("Number of toots should be between 1 and 20.")
    return n


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

timeline_args = common_timeline_args + [
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
        arguments=[account_arg],
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
]

TUI_COMMANDS = [
    Command(
        name="tui",
        description="Launches the toot terminal user interface",
        arguments=[],
        require_auth=True,
    ),
]


READ_COMMANDS = [
    Command(
        name="whoami",
        description="Display logged in user details",
        arguments=[],
        require_auth=True,
    ),
    Command(
        name="whois",
        description="Display account details",
        arguments=[
            (["account"], {
                "help": "account name or numeric ID"
            }),
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
        ],
        require_auth=True,
    ),
    Command(
        name="timeline",
        description="Show recent items in a timeline (home by default)",
        arguments=timeline_args,
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
            (["-v", "--visibility"], {
                "type": visibility,
                "default": "public",
                "help": 'post visibility, one of: %s' % ", ".join(VISIBILITY_CHOICES),
            }),
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
                "help": "ISO 639-2 language code of the toot, to skip automatic detection",
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
            (["-t", "--content-type"], {
                "type": str,
                "help": "MIME type for the status text (not supported on all instances)",
            }),
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
        arguments=[status_id_arg],
        require_auth=True,
    ),
    Command(
        name="favourite",
        description="Favourite a status",
        arguments=[status_id_arg],
        require_auth=True,
    ),
    Command(
        name="unfavourite",
        description="Unfavourite a status",
        arguments=[status_id_arg],
        require_auth=True,
    ),
    Command(
        name="reblog",
        description="Reblog a status",
        arguments=[status_id_arg],
        require_auth=True,
    ),
    Command(
        name="unreblog",
        description="Unreblog a status",
        arguments=[status_id_arg],
        require_auth=True,
    ),
    Command(
        name="reblogged_by",
        description="Show accounts that reblogged the status",
        arguments=[status_id_arg],
        require_auth=False,
    ),
    Command(
        name="pin",
        description="Pin a status",
        arguments=[status_id_arg],
        require_auth=True,
    ),
    Command(
        name="unpin",
        description="Unpin a status",
        arguments=[status_id_arg],
        require_auth=True,
    ),
    Command(
        name="bookmark",
        description="Bookmark a status",
        arguments=[status_id_arg],
        require_auth=True,
    ),
    Command(
        name="unbookmark",
        description="Unbookmark a status",
        arguments=[status_id_arg],
        require_auth=True,
    ),
]

ACCOUNTS_COMMANDS = [
    Command(
        name="follow",
        description="Follow an account",
        arguments=[
            account_arg,
        ],
        require_auth=True,
    ),
    Command(
        name="unfollow",
        description="Unfollow an account",
        arguments=[
            account_arg,
        ],
        require_auth=True,
    ),
    Command(
        name="following",
        description="List accounts following the given account",
        arguments=[
            account_arg,
        ],
        require_auth=True,
    ),
    Command(
        name="followers",
        description="List accounts followed by the given account",
        arguments=[
            account_arg,
        ],
        require_auth=True,
    ),
    Command(
        name="mute",
        description="Mute an account",
        arguments=[
            account_arg,
        ],
        require_auth=True,
    ),
    Command(
        name="unmute",
        description="Unmute an account",
        arguments=[
            account_arg,
        ],
        require_auth=True,
    ),
    Command(
        name="block",
        description="Block an account",
        arguments=[
            account_arg,
        ],
        require_auth=True,
    ),
    Command(
        name="unblock",
        description="Unblock an account",
        arguments=[
            account_arg,
        ],
        require_auth=True,
    ),
]

COMMANDS = AUTH_COMMANDS + READ_COMMANDS + TUI_COMMANDS + POST_COMMANDS + STATUS_COMMANDS + ACCOUNTS_COMMANDS


def print_usage():
    max_name_len = max(len(command.name) for command in COMMANDS)

    groups = [
        ("Authentication", AUTH_COMMANDS),
        ("TUI", TUI_COMMANDS),
        ("Read", READ_COMMANDS),
        ("Post", POST_COMMANDS),
        ("Status", STATUS_COMMANDS),
        ("Accounts", ACCOUNTS_COMMANDS),
    ]

    print_out("<green>{}</green>".format(CLIENT_NAME))
    print_out("<blue>v{}</blue>".format(__version__))

    for name, cmds in groups:
        print_out("")
        print_out(name + ":")

        for cmd in cmds:
            cmd_name = cmd.name.ljust(max_name_len + 2)
            print_out("  <yellow>toot {}</yellow> {}".format(cmd_name, cmd.description))

    print_out("")
    print_out("To get help for each command run:")
    print_out("  <yellow>toot <command> --help</yellow>")
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

    for args, kwargs in combined_args:
        parser.add_argument(*args, **kwargs)

    return parser


def run_command(app, user, name, args):
    command = next((c for c in COMMANDS if c.name == name), None)

    if not command:
        print_err("Unknown command '{}'\n".format(name))
        print_usage()
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
    # Enable debug logging if --debug is in args
    if "--debug" in sys.argv:
        filename = os.getenv("TOOT_LOG_FILE")
        logging.basicConfig(level=logging.DEBUG, filename=filename)

    command_name = sys.argv[1] if len(sys.argv) > 1 else None
    args = sys.argv[2:]

    if not command_name:
        return print_usage()

    user, app = config.get_active_user_app()

    try:
        run_command(app, user, command_name, args)
    except (ConsoleError, ApiError) as e:
        print_err(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        pass
