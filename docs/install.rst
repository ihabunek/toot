============
Installation
============

toot is packaged for various platforms.

.. contents::
    :local:
    :backlinks: none

.. warning::

    There used to be an **APT package repository** at `bezdomni.net`, managed by
    myself. Since toot is now available in the Debian and Ubuntu repos, the repo
    is no longer required and will be removed soon.

    If you have previously added the repository, remove it by deleting the file
    at: ``/etc/apt/sources.list.d/bezdomni.list``.

Overview
--------

Packaging overview provided by `repology.org <https://repology.org/project/toot/versions>`_.

.. image :: https://repology.org/badge/vertical-allrepos/toot.svg
   :alt: Packaging status
   :target: https://repology.org/project/toot/versions

Debian & Ubuntu
---------------

Since Debian 10 (buster) and Ubuntu 19.04 (disco), toot is available in the
official package repository.

.. code-block:: bash

    sudo apt install toot

Debian package is maintained by `Jonathan Carter <https://mastodon.xyz/@highvoltage>`_.


Arch Linux
----------

Install from `AUR <https://aur.archlinux.org/packages/toot/>`_.

.. code-block:: bash

    yay -S toot

FreeBSD ports
-------------

Install the package:

.. code-block:: bash

    pkg install py38-toot

Build and install from sources:

.. code-block:: bash

    cd /usr/ports/net-im/toot
    make install

FreeBSD port is maintained by `Mateusz Piotrowski <https://mastodon.social/@mpts>`_

Nixpkgs
-------

This works on NixOS or systems with the Nix package manager installed.

.. code-block:: bash

    nix-env -iA nixos.toot


OpenBSD ports
-------------

Install the package:

.. code-block:: bash

    pkg_add toot

Build and install from sources:

.. code-block:: bash

    cd /usr/ports/net/toot
    make install

OpenBSD port is maintained by `Klemens Nanni <mailto:kl3@posteo.org>`_

Python Package Index
--------------------

Install from PyPI using pip, preferably into a virtual environment.

.. code-block:: bash

    pip install --user toot

Homebrew
--------------------

This works on Mac OSX with `homebrew <https://brew.sh/>`_ installed.
Tested with on Catalina, Mojave, and High Sierra.

.. code-block:: bash

    brew update
    brew install toot

Source
------

Finally, you can get the latest source distribution, wheel or debian package
`from GitHub <https://github.com/ihabunek/toot/releases/latest/>`_.
