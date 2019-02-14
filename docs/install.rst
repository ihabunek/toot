============
Installation
============

toot is packaged for various platforms.

.. contents::
    :local:
    :backlinks: none

Debian Buster
-------------

If you're running Debian Buster (testing), toot is available in the Debian package repository.

.. code-block:: bash

    sudo apt install toot

Debian package is maintained by `Jonathan Carter <https://mastodon.xyz/@highvoltage>`_.


APT package repository
----------------------

This works for Debian, Ubuntu and derivatives. The repo is signed with my
`keybase.io <https://keybase.io/ihabunek>`_ key.

Add the `bezdomni.net` repository:

.. code-block:: bash

    echo "deb http://bezdomni.net/packages/ ./" | sudo tee /etc/apt/sources.list.d/bezdomni.list
    curl https://keybase.io/ihabunek/pgp_keys.asc | sudo apt-key add -

Install the package:

.. code-block:: bash

    sudo apt update
    sudo apt install python3-toot

Arch Linux
----------

Install from `AUR <https://aur.archlinux.org/packages/toot/>`_.

..code-block:: bash

    yay -S toot

FreeBSD ports
-------------

Install the package:

.. code-block:: bash

    pkg install py36-toot

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

Install from PyPI using pip, preferably into a virtual environment:

.. code-block:: bash

    pip install toot

Source
------

Finally, you can get the latest source distribution, wheel or debian package
`from Github <https://github.com/ihabunek/toot/releases/latest/>`_.
