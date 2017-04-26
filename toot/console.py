# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import os
import sys
import logging

from argparse import ArgumentParser, FileType
from collections import namedtuple
from toot import config, api, commands, ConsoleError, CLIENT_NAME, CLIENT_WEBSITE
from toot.output import print_error


VISIBILITY_CHOICES = ['public', 'unlisted', 'private', 'direct']


def visibility(value):
    """Validates the visibilty parameter"""
    if value not in VISIBILITY_CHOICES:
        raise ValueError("Invalid visibility value")

    return value


Command = namedtuple("Command", ["name", "description", "require_auth", "arguments"])


# Some common arguments:
account_arg = (["account"], {
    "help": "account name, e.g. 'Gargron' or 'polymerwitch@toot.cat'",
})


COMMANDS = [
    Command(
        name="login",
        description="Log into a Mastodon instance",
        arguments=[],
        require_auth=False,
    ),
    Command(
        name="login_2fa",
        description="Log in using two factor authentication (experimental)",
        arguments=[],
        require_auth=False,
    ),
    Command(
        name="logout",
        description="Log out, delete stored access keys",
        arguments=[],
        require_auth=False,
    ),
    Command(
        name="auth",
        description="Show stored credentials",
        arguments=[],
        require_auth=False,
    ),
    Command(
        name="whoami",
        description="Display logged in user details",
        arguments=[],
        require_auth=True,
    ),
    Command(
        name="whois",
        description="Display user details",
        arguments=[
            (["account"], {
                "help": "account name or numeric ID"
            }),
        ],
        require_auth=True,
    ),
    Command(
        name="post",
        description="Post a status text to your timeline",
        arguments=[
            (["text"], {
                "help": "The status text to post.",
            }),
            (["-m", "--media"], {
                "type": FileType('rb'),
                "help": "path to the media file to attach"
            }),
            (["-v", "--visibility"], {
                "type": visibility,
                "default": "public",
                "help": 'post visibility, one of: %s' % ", ".join(VISIBILITY_CHOICES),
            })
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
    Command(
        name="timeline",
        description="Show recent items in your public timeline",
        arguments=[],
        require_auth=True,
    ),
    Command(
        name="curses",
        description="An experimental timeline app.",
        arguments=[],
        require_auth=True,
    ),
]


def print_usage():
    print(CLIENT_NAME)
    print("")
    print("Usage:")

    max_name_len = max(len(command.name) for command in COMMANDS)

    for command in COMMANDS:
        print("  toot", command.name.ljust(max_name_len + 2), command.description)

    print("")
    print("To get help for each command run:")
    print("  toot <command> --help")
    print("")
    print(CLIENT_WEBSITE)


def get_argument_parser(name, command):
    parser = ArgumentParser(
        prog='toot %s' % name,
        description=command.description,
        epilog=CLIENT_WEBSITE)

    for args, kwargs in command.arguments:
        parser.add_argument(*args, **kwargs)

    return parser


def run_command(app, user, name, args):
    command = next((c for c in COMMANDS if c.name == name), None)

    if not command:
        print_error("Unknown command '{}'\n".format(name))
        print_usage()
        return

    parser = get_argument_parser(name, command)
    parsed_args = parser.parse_args(args)

    if command.require_auth and (not user or not app):
        print_error("This command requires that you are logged in.")
        print_error("Please run `toot login` first.")
        return

    fn = commands.__dict__.get(name)

    if not fn:
        raise NotImplementedError("Command '{}' does not have an implementation.".format(name))

    return fn(app, user, parsed_args)


def main():
    if os.getenv('TOOT_DEBUG'):
        logging.basicConfig(level=logging.DEBUG)

    # If something is piped in, append it to commandline arguments
    if not sys.stdin.isatty():
        sys.argv.append(sys.stdin.read())

    command_name = sys.argv[1] if len(sys.argv) > 1 else None
    args = sys.argv[2:]

    if not command_name:
        return print_usage()

    user = config.load_user()
    app = config.load_app(user.instance) if user else None

    try:
        run_command(app, user, command_name, args)
    except ConsoleError as e:
        print_error(str(e))
    except api.ApiError as e:
        print_error(str(e))
