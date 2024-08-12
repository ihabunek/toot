============================
Toot - a Mastodon CLI client
============================

.. image:: https://raw.githubusercontent.com/ihabunek/toot/master/trumpet.png

Toot is a CLI and TUI tool for interacting with Mastodon instances from the command line.

.. image:: https://img.shields.io/badge/author-%40ihabunek-blue.svg?maxAge=3600&style=flat-square
   :target: https://mastodon.social/@ihabunek
.. image:: https://img.shields.io/github/license/ihabunek/toot.svg?maxAge=3600&style=flat-square
   :target: https://opensource.org/licenses/GPL-3.0
.. image:: https://img.shields.io/pypi/v/toot.svg?maxAge=3600&style=flat-square
   :target: https://pypi.python.org/pypi/toot

Resources
---------

* Homepage: https://github.com/ihabunek/toot
* Issues: https://github.com/ihabunek/toot/issues
* Documentation: https://toot.bezdomni.net/
* Mailing list for discussion, support and patches:
  https://lists.sr.ht/~ihabunek/toot-discuss
* Informal discussion: #toot IRC channel on `libera.chat <https://libera.chat/>`_

Features
--------

* Posting, replying, deleting statuses
* Support for media uploads, spoiler text, sensitive content
* Search by account or hash tag
* Following, muting and blocking accounts
* Simple switching between authenticated in Mastodon accounts

Terminal User Interface
-----------------------

toot includes a terminal user interface (TUI). Run it with ``toot tui``.

TUI Features:
-------------

* Block graphic image display (requires optional libraries `pillow <https://pypi.org/project/pillow/>`, `term-image <https://pypi.org/project/term-image/>`, and `urwidgets <https://pypi.org/project/urwidgets/>`)
* Bitmapped image display in `kitty <https://sw.kovidgoyal.net/kitty/>` terminal ``toot tui -f kitty``
* Bitmapped image display in `iTerm2 <https://iterm2.com/>`, or `WezTerm <https://wezfurlong.org/wezterm/index.html>` terminal ``toot tui -f iterm``


.. image :: https://raw.githubusercontent.com/ihabunek/toot/master/docs/images/tui_list.png

.. image :: https://raw.githubusercontent.com/ihabunek/toot/master/docs/images/tui_compose.png

License
-------

Copyright Ivan Habunek <ivan@habunek.com> and contributors.

Licensed under `GPLv3 <http://www.gnu.org/licenses/gpl-3.0.html>`_, see `LICENSE <LICENSE>`_.
