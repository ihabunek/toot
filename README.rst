=============================
Toot - Mastodon CLI interface
=============================

Interact with Mastodon social networks from the command line.

.. image:: https://img.shields.io/travis/ihabunek/toot.svg?maxAge=3600&style=flat-square
   :target: https://travis-ci.org/ihabunek/toot
.. image:: https://img.shields.io/badge/author-%40ihabunek-blue.svg?maxAge=3600&style=flat-square
   :target: https://mastodon.social/@ihabunek
.. image:: https://img.shields.io/github/license/ihabunek/pdf417-py.svg?maxAge=3600&style=flat-square
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

===================  ===============================================================
 Command              Description
===================  ===============================================================
 ``toot login``       Log into a Mastodon instance.
 ``toot 2fa``         Log into a Mastodon instance using two factor authentication.
 ``toot logout``      Log out, deletes stored access keys.
 ``toot auth``        Display stored authenitication tokens.
 ``toot whoami``      Display logged in user details.
 ``toot post``        Post a status to your timeline.
 ``toot search``      Search for accounts or hashtags.
 ``toot timeline``    Display recent items in your public timeline.
 ``toot follow``      Follow an account.
 ``toot unfollow``    Unfollow an account.
===================  ===============================================================

Authentication
--------------

Before tooting, you need to login to a Mastodon instance:

.. code-block::

    toot login

**Two factor authentication** is supported experimentally, instead of ``login``, you should instead run:

.. code-block::

    toot 2fa

You will be asked to chose an instance_ and enter your credentials.

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
