# -*- coding: utf-8 -*-

from collections import namedtuple

App = namedtuple('App', ['instance', 'base_url', 'client_id', 'client_secret'])
User = namedtuple('User', ['instance', 'username', 'access_token'])

DEFAULT_INSTANCE = 'mastodon.social'

CLIENT_NAME = 'toot - Mastodon CLI Interface'
CLIENT_WEBSITE = 'https://github.com/ihabunek/toot'
