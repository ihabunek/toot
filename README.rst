=============================
Toot - Mastodon CLI interface
=============================

Interact with Mastodon social networks from the command line.

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

Firstly, you will need to login to a Mastodon instance:

.. code-block::

    toot login

You will be asked to chose an instance_ and enter your credentials.

.. _instance: https://github.com/tootsuite/documentation/blob/master/Using-Mastodon/List-of-Mastodon-instances.md

The application and user access tokens will be saved in two files in your home directory:

* ``~/.config/toot/app.cfg``
* ``~/.config/toot/user.cfg``

You can check whether you are currently logged in:

.. code-block::

    toot auth

And you can logout which will remove the stored access tokens:

.. code-block::

    toot logout

Show timeline
~~~~~~~~~~~~~

To show recent items in your public timeline:

.. code-block::

    toot timeline

Post status
~~~~~~~~~~~

To post a new status to your timeline:

.. code-block::

    toot post "Hello world!"

Optionally attach an image or video to the status:

    toot post "Hello world!" --media=path/to/world.jpg

To set post visibility:

    toot post "Hello world!" --visibility=unlisted

Possible visibility values are: ``public`` (default), ``unlisted``, ``private``, ``direct``. They are documented  `here <https://github.com/tootsuite/documentation/blob/aa20089756c8cf9ff5a52fb35ad1a9472f10970c/Using-Mastodon/User-guide.md#toot-privacy>`_.
