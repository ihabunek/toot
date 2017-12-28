# -*- coding: utf-8 -*-

import sys
import logging

from argparse import ArgumentParser, FileType
from collections import namedtuple
from toot import config, api, commands, ConsoleError, CLIENT_NAME, CLIENT_WEBSITE
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
    (["--debug"], {
        "help": "show debug log in console",
        "action": 'store_true',
        "default": False,
    })
]

account_arg = (["account"], {
    "help": "account name, e.g. 'Gargron' or 'polymerwitch@toot.cat'",
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
        description="Log into a Mastodon instance, does NOT support two factor authentication",
        arguments=[instance_arg, email_arg],
        require_auth=False,
    ),
    Command(
        name="login_browser",
        description="Log in using your browser, supports regular and two factor authentication",
        arguments=[instance_arg, email_arg],
        require_auth=False,
    ),
    Command(
        name="login_2fa",
        description="Log in using two factor authentication in the console (hacky, experimental)",
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
        description="Show recent items in your public timeline",
        arguments=[],
        require_auth=True,
    ),
    Command(
        name="curses",
        description="An experimental timeline app (doesn't work on Windows)",
        arguments=[],
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

    return parser


def run_command(app, user, name, args):
    command = next((c for c in COMMANDS if c.name == name), None)

    if not command:
        print_err("Unknown command '{}'\n".format(name))
        print_usage()
        return

    parser = get_argument_parser(name, command)
    parsed_args = parser.parse_args(args)

    if command.require_auth and (not user or not app):
        print_err("This command requires that you are logged in.")
        print_err("Please run `toot login` first.")
        return

    fn = commands.__dict__.get(name)

    if not fn:
        raise NotImplementedError("Command '{}' does not have an implementation.".format(name))

    return fn(app, user, parsed_args)


def main():
    # Enable debug log if --debug is in args
    if "--debug" in sys.argv:
        logging.basicConfig(level=logging.DEBUG)

    # If something is piped in, append it to commandline arguments
    if not sys.stdin.isatty():
        stdin = sys.stdin.read()
        if stdin:
            sys.argv.append(stdin)

    command_name = sys.argv[1] if len(sys.argv) > 1 else None
    args = sys.argv[2:]

    if not command_name:
        return print_usage()

    user = config.load_user()
    app = config.load_app(user.instance) if user else None

    try:
        run_command(app, user, command_name, args)
    except ConsoleError as e:
        print_err(str(e))
        sys.exit(1)
    except api.ApiError as e:
        print_err(str(e))
        sys.exit(1)
