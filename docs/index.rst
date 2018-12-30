toot - Mastodon CLI client
==========================

.. image:: _static/trumpet.png

toot is a commandline tool for interacting with Mastodon social networks.

.. image:: https://img.shields.io/travis/ihabunek/toot.svg?maxAge=3600&style=flat-square
   :target: https://travis-ci.org/ihabunek/toot
.. image:: https://img.shields.io/badge/author-%40ihabunek-blue.svg?maxAge=3600&style=flat-square
   :target: https://mastodon.social/@ihabunek
.. image:: https://img.shields.io/github/license/ihabunek/toot.svg?maxAge=3600&style=flat-square
   :target: https://opensource.org/licenses/MIT
.. image:: https://img.shields.io/pypi/v/toot.svg?maxAge=3600&style=flat-square
   :target: https://pypi.python.org/pypi/toot

Features
--------

* Posting, replying, deleting statuses
* Support for media uploads, spoiler text, sensitive content
* Search by account or hash tag
* Following, muting and blocking accounts
* Simple switching between multiple Mastodon accounts

Contents
--------

.. toctree::
   :maxdepth: 2

   install
   usage
   advanced
   release

Curses UI
---------

toot has an experimental curses based console UI. Run it with ``toot curses``.

.. image :: _static/curses.png

Development
-----------

The project source code and issue tracker are available on GitHub:

https://github.com/ihabunek/toot

Please report any issues there. Pull requests are welcome.

License
-------

Copyright 2018 Ivan Habunek <ivan@habunek.com>

Licensed under `GPLv3 <http://www.gnu.org/licenses/gpl-3.0.html>`_.
