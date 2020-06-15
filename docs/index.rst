toot - Mastodon CLI client
==========================

.. image:: _static/trumpet.png

Toot is a CLI and TUI tool for interacting with Mastodon instances from the command line.

.. image:: https://img.shields.io/travis/ihabunek/toot.svg?maxAge=3600&style=flat-square
   :target: https://travis-ci.org/ihabunek/toot
.. image:: https://img.shields.io/badge/author-%40ihabunek-blue.svg?maxAge=3600&style=flat-square
   :target: https://mastodon.social/@ihabunek
.. image:: https://img.shields.io/github/license/ihabunek/toot.svg?maxAge=3600&style=flat-square
   :target: https://opensource.org/licenses/MIT
.. image:: https://img.shields.io/pypi/v/toot.svg?maxAge=3600&style=flat-square
   :target: https://pypi.python.org/pypi/toot

Resources
---------

* Homepage: https://github.com/ihabunek/toot
* Issues: https://github.com/ihabunek/toot/issues
* Documentation: https://toot.readthedocs.io/en/latest/
* Discussion and support: `#toot IRC channel on freenode.net
  <https://webchat.freenode.net/?channels=toot>`_

Features
--------

* Posting, replying, deleting, favouriting, reblogging & pinning statuses
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

toot includes a curses-based terminal user interface (TUI). Run it with ``toot tui``.

.. image :: _static/tui_list.png

.. image :: _static/tui_poll.png

.. image :: _static/tui_compose.png

Development
-----------

The project source code and issue tracker are available on GitHub:

https://github.com/ihabunek/toot

Please report any issues there. Pull requests are welcome.

License
-------

Copyright Ivan Habunek <ivan@habunek.com> and contributors.

Licensed under `GPLv3 <http://www.gnu.org/licenses/gpl-3.0.html>`_.
