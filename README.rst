============================
Toot - a Mastodon CLI client
============================

Interact with Mastodon social networks from the command line.

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

Install using pip:

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
      toot login           Log into a Mastodon instance, does NOT support two factor authentication
      toot login_browser   Log in using your browser, supports regular and two factor authentication
      toot login_2fa       Log in using two factor authentication in the console (hacky, experimental)
      toot logout          Log out, delete stored access keys
      toot auth            Show stored credentials

    Read:
      toot whoami          Display logged in user details
      toot whois           Display account details
      toot search          Search for users or hashtags
      toot timeline        Show recent items in your public timeline
      toot curses          An experimental timeline app.

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

The application and user access tokens will be saved in two files in your home directory:

* ``~/.config/toot/instances/<name>`` - created for each mastodon instance once
* ``~/.config/toot/user.cfg``

You can check whether you are currently logged in:

.. code-block::

    toot auth

And you can logout which will remove the stored access tokens:

.. code-block::

    toot logout

License
-------

Copyright © 2017 Ivan Habunek <ivan@habunek.com>

Licensed under the GPLv3: http://www.gnu.org/licenses/gpl-3.0.html
