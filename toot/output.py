# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import sys


def _color(text, color):
    return "\033[3{}m{}\033[0m".format(color, text)


def red(text):
    return _color(text, 1)


def green(text):
    return _color(text, 2)


def yellow(text):
    return _color(text, 3)


def blue(text):
    return _color(text, 4)


def magenta(text):
    return _color(text, 5)


def cyan(text):
    return _color(text, 6)


def print_error(text):
    print(red(text), file=sys.stderr)
