=================
Release procedure
=================

This document is a checklist for creating a toot release.

Currently the process is pretty manual and would benefit from automatization.

Bump & tag version
------------------

* Update the version number in ``setup.py``
* Update the version number in ``toot/__init__.py``
* Update the ``CHANGELOG.md`` with the release notes & date
* Tag a release in git
* Push master & tag to GitHub

Publishing to PyPI
------------------

* ``make dist`` to create source and wheel distributions
* ``make publish`` to push them to PyPI

Publishing to Debian repo
-------------------------

Publishing deb packages is done via `ihabunek/packages <https://github.com/ihabunek/packages>`_.

* run ``make deb_dist`` to create the debian package
* copy deb file to packages project directory
* in packages project directory:
    * ``make`` to build the repo files
    * ``make publish`` to send them to the server

Github release
--------------

* `Create a release <https://github.com/ihabunek/toot/releases/>`_ for the newly
  pushed tag, paste changelog since last tag in the description
* Upload the assets generated in previous two steps to the release:
    * source dist (.zip and .tar.gz)
    * wheel distribution (.whl)
    * debian package (.deb)
