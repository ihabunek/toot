# -*- coding: utf-8 -*-

import sys
import re

from textwrap import wrap
from toot.utils import format_content

START_CODES = {
    'red':     '\033[31m',
    'green':   '\033[32m',
    'yellow':  '\033[33m',
    'blue':    '\033[34m',
    'magenta': '\033[35m',
    'cyan':    '\033[36m',
}

END_CODE = '\033[0m'

START_PATTERN = "<(" + "|".join(START_CODES.keys()) + ")>"

END_PATTERN = "</(" + "|".join(START_CODES.keys()) + ")>"


def start_code(match):
    name = match.group(1)
    return START_CODES[name]


def colorize(text):
    text = re.sub(START_PATTERN, start_code, text)
    text = re.sub(END_PATTERN, END_CODE, text)

    return text


def strip_tags(text):
    text = re.sub(START_PATTERN, '', text)
    text = re.sub(END_PATTERN, '', text)

    return text


USE_ANSI_COLOR = "--no-color" not in sys.argv


def print_out(*args, **kwargs):
    args = [colorize(a) if USE_ANSI_COLOR else strip_tags(a) for a in args]
    print(*args, **kwargs)


def print_err(*args, **kwargs):
    args = ["<red>{}</red>".format(a) for a in args]
    args = [colorize(a) if USE_ANSI_COLOR else strip_tags(a) for a in args]
    print(*args, file=sys.stderr, **kwargs)


def print_instance(instance):
    print_out("<green>{}</green>".format(instance['title']))
    print_out("<blue>{}</blue>".format(instance['uri']))
    print_out("running Mastodon {}".format(instance['version']))
    print_out("")

    description = instance['description'].strip()
    if not description:
        return

    lines = [line.strip() for line in format_content(description) if line.strip()]
    for line in lines:
        for l in wrap(line.strip()):
            print(l)
        print()
