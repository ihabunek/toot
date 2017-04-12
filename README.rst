====
Toot
====

Post to Mastodon social networks from the command line.


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
