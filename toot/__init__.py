# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from collections import namedtuple

App = namedtuple('App', ['instance', 'base_url', 'client_id', 'client_secret'])
User = namedtuple('User', ['instance', 'username', 'access_token'])

DEFAULT_INSTANCE = 'mastodon.social'

CLIENT_NAME = 'toot - a Mastodon CLI client'
CLIENT_WEBSITE = 'https://github.com/ihabunek/toot'


class ConsoleError(Exception):
    pass
