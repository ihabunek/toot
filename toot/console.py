# -*- coding: utf-8 -*-

import os
import sys
import logging

from argparse import ArgumentParser, FileType
from collections import namedtuple
from toot import config, commands, CLIENT_NAME, CLIENT_WEBSITE, __version__
from toot.exceptions import ApiError, ConsoleError
from toot.output import print_out, print_err

VISIBILITY_CHOICES = ['public', 'unlisted', 'private', 'direct']


def visibility(value):
    """Validates the visibilty parameter"""
    if value not in VISIBILITY_CHOICES:
        raise ValueError("Invalid visibility value")

    return value


Command = namedtuple("Command", ["name", "description", "require_auth", "arguments"])


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
    })
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


AUTH_COMMANDS = [
    Command(
        name="login",
        description="Log into a mastodon instance using your browser (recommended)",
        arguments=[instance_arg],
        require_auth=False,
    ),
    Command(
        name="login_cli",
        description="Log in from the console, does NOT support two factor authentication",
        arguments=[instance_arg, email_arg],
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
        name="instance",
        description="Display instance details",
        arguments=[
            (["instance"], {
                "help": "instance domain (e.g. 'mastodon.social') or blank to use current",
                "nargs": "?",
            }),

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
        name="timeline",
        description="Show recent items in a timeline (home by default)",
        arguments=[
            (["-p", "--public"], {
                "action": "store_true",
                "default": False,
                "help": "Show public timeline.",
            }),
            (["-t", "--tag"], {
                "type": str,
                "help": "Show timeline for given hashtag.",
            }),
            (["-i", "--list"], {
                "type": int,
                "help": "Show timeline for given list ID.",
            }),
            (["-l", "--local"], {
                "action": "store_true",
                "default": False,
                "help": "Show only statuses from local instance (public and tag timelines only).",
            }),
        ],
        require_auth=True,
    ),
    Command(
        name="curses",
        description="An experimental timeline app (doesn't work on Windows)",
        arguments=[
            (["-p", "--public"], {
                "action": 'store_true',
                "default": False,
                "help": "Resolve non-local accounts",
            }),
            (["-i", "--instance"], {
                "type": str,
                "help": 'instance from which to read (for public timeline only)',
            })
        ],
        require_auth=False,
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
                "type": FileType('rb'),
                "help": "path to the media file to attach"
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
                "help": 'text to be shown as a warning before the actual content',
            }),
            (["-r", "--reply-to"], {
                "type": int,
                "help": 'local ID of the status you want to reply to',
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
            })
        ],
        require_auth=True,
    ),
    Command(
        name="delete",
        description="Delete an existing status",
        arguments=[
            (["status_id"], {
                "help": "ID of the status to delete",
                "type": int,
            })
        ],
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

COMMANDS = AUTH_COMMANDS + READ_COMMANDS + POST_COMMANDS + ACCOUNTS_COMMANDS


def print_usage():
    max_name_len = max(len(command.name) for command in COMMANDS)

    groups = [
        ("Authentication", AUTH_COMMANDS),
        ("Read", READ_COMMANDS),
        ("Post", POST_COMMANDS),
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

    for args, kwargs in command.arguments + common_args:
        parser.add_argument(*args, **kwargs)

    # If the command requires auth, give an option to select account
    if command.require_auth:
        parser.add_argument("-u", "--using", help="the account to use, overrides active account")

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

    # If something is piped in, append it to commandline arguments
    if not sys.stdin.isatty():
        stdin = sys.stdin.read()
        if stdin:
            sys.argv.append(stdin)

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
    except KeyboardInterrupt as e:
        pass
