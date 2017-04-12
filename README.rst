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

Currently implements only posting a new status:


.. code-block::

    toot post "Hello world!"

On first use, you will be asked to choose a Mastodon instance and log in.

The app and user tokens are saved in two files in your home directory:

* ``~/.config/toot/app.cfg``
* ``~/.config/toot/user.cfg``

To logout, delete these files.
