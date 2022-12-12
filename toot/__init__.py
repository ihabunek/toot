# -*- coding: utf-8 -*-

from collections import namedtuple

__version__ = '0.32.1'

App = namedtuple('App', ['instance', 'base_url', 'client_id', 'client_secret'])
User = namedtuple('User', ['instance', 'username', 'access_token'])

DEFAULT_INSTANCE = 'mastodon.social'

CLIENT_NAME = 'toot - a Mastodon CLI client'
CLIENT_WEBSITE = 'https://github.com/ihabunek/toot'
