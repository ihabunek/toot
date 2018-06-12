============================
Toot - a Mastodon CLI client
============================

Interact with Mastodon social network from the command line.

.. image:: https://img.shields.io/travis/ihabunek/toot.svg?maxAge=3600&style=flat-square
   :target: https://travis-ci.org/ihabunek/toot
.. image:: https://img.shields.io/badge/author-%40ihabunek-blue.svg?maxAge=3600&style=flat-square
   :target: https://mastodon.social/@ihabunek
.. image:: https://img.shields.io/github/license/ihabunek/toot.svg?maxAge=3600&style=flat-square
   :target: https://opensource.org/licenses/MIT
.. image:: https://img.shields.io/pypi/v/toot.svg?maxAge=3600&style=flat-square
   :target: https://pypi.python.org/pypi/toot


Installation
------------

Debian Buster
~~~~~~~~~~~~~

If you're running Debian Buster (testing), toot is available in the Debian
package repository.

.. code-block::

    sudo apt install toot

Debian package is maintained by [Jonathan Carter](https://mastodon.xyz/@highvoltage).


From APT package repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This works for Debian, Ubuntu and derivatives.

The repo is signed with my `keybase.io <https://keybase.io/ihabunek>`_ key.

Add the `bezdomni.net` repository:

.. code-block::

    echo "deb http://bezdomni.net/packages/ ./" | sudo tee /etc/apt/sources.list.d/bezdomni.list
    curl https://keybase.io/ihabunek/pgp_keys.asc | sudo apt-key add -

Install the package:

.. code-block::

    sudo apt update
    sudo apt install python3-toot

From FreeBSD ports
~~~~~~~~~~~~~~~~~~

Install the package:

.. code-block::

    pkg install py36-toot

Build and install from sources:

.. code-block::

    cd /usr/ports/net-im/toot
    make install

FreeBSD port is maintained by [Mateusz Piotrowski](https://mastodon.social/@mpts)

From Nixpkgs
~~~~~~~~~~~~

This works on NixOS or systems with the Nix package manager installed.

.. code-block::

    nix-env -iA nixos.toot


From OpenBSD ports
~~~~~~~~~~~~~~~~~~

Install the package:

.. code-block::

    pkg_add toot

Build and install from sources:

.. code-block::

    cd /usr/ports/net/toot
    make install

Thanks to `Klemens Nanni <mailto:kl3@posteo.org>`_ for handling the OpenBSD ports.

From Python Package Index
~~~~~~~~~~~~~~~~~~~~~~~~~

Otherwise, install from PyPI using pip, preferably into a virtual environment:

.. code-block::

    pip install toot

Usage
-----

Running ``toot`` displays a list of available commands.

Running ``toot <command> -h`` shows the documentation for the given command.

.. code-block::

    $ toot

    toot - a Mastodon CLI client

    Authentication:
      toot login           Log in from the console, does NOT support two factor authentication
      toot login_browser   Log in using your browser, supports regular and two factor authentication
      toot activate        Switch between logged in accounts.
      toot logout          Log out, delete stored access keys
      toot auth            Show logged in accounts and instances

    Read:
      toot whoami          Display logged in user details
      toot whois           Display account details
      toot instance        Display instance details
      toot search          Search for users or hashtags
      toot timeline        Show recent items in a timeline (home by default)
      toot curses          An experimental timeline app (doesn't work on Windows)

    Post:
      toot post            Post a status text to your timeline
      toot upload          Upload an image or video file

    Accounts:
      toot follow          Follow an account
      toot unfollow        Unfollow an account
      toot mute            Mute an account
      toot unmute          Unmute an account
      toot block           Block an account
      toot unblock         Unblock an account

    To get help for each command run:
      toot <command> --help

    https://github.com/ihabunek/toot

It is possible to pipe status text into `toot post`, for example:

.. code-block::

    echo "Text to post" | toot post
    cat mypost.txt | toot post


Authentication
--------------

Before tooting, you need to login to a Mastodon instance.

If you don't use two factor authentication you can log in directly from the command line:

.. code-block::

    toot login

You will be asked to chose an instance_ and enter your credentials.

If you do use **two factor authentication**, you need to log in through your browser:

.. code-block::

    toot login_browser

You will be redirected to your Mastodon instance to log in and authorize toot to access your account, and will be given an **authorization code** in return which you need to enter to log in.

.. _instance: https://github.com/tootsuite/documentation/blob/master/Using-Mastodon/List-of-Mastodon-instances.md

The application and user access tokens will be saved in the configuration file located at ``~/.config/toot/instances/config.json``.

It's possible to be logged into **multiple accounts** at the same time. Just repeat the above process for another instance. You can see all logged in accounts by running ``toot auth``. The currently active account will have an **ACTIVE** flag next to it.

To switch accounts, use ``toot activate``. Alternatively, most commands accept a ``--using`` option which can be used to specify the account you wish to use just that one time.

Finally you can logout from an account by using ``toot logout``. This will remove the stored access tokens for that account.

License
-------

Copyright 2017 Ivan Habunek <ivan@habunek.com>

Licensed under the GPLv3: http://www.gnu.org/licenses/gpl-3.0.html
