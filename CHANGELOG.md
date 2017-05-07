Changelog
---------

**0.11.0 (2016-05-07)**

* Fix error when running toot from crontab (#11)
* Minor tweaks

**0.10.0 (2016-04-26)**

* Add commands: `block`, `unblock`, `mute`, `unmute`
* Internal improvements

**0.9.1 (2016-04-24)**

* Fix conflict with curses package name

**0.9.0 (2016-04-21)**

* Add `whois` command
* Add experimental `curses` app for viewing the timeline

**0.8.0 (2016-04-19)**

* Renamed command `2fa` to `login_2fa` **BC BREAK**
* It is now possible to pipe text into `toot post`

**0.7.0 (2016-04-18)**

* Experimental 2FA support (#3)
* Do not create a new application for each login
* **Warning**: Due to changes in configuration format, after upgrading to this
  version, you will be required to log in to your Mastodon instance again.

**0.6.0 (2016-04-17)**

* Add `whoami` command
* Migrate from `optparse` to `argparse`

**0.5.0 (2016-04-16)**

* Add `search`, `follow` and `unfollow` commands
* Migrate from `optparse` to `argparse`

**0.4.0 (2016-04-15)**

* Add `upload` command to post media
* Add `--visibility` and `--media` options to `post` command

**0.3.0 (2016-04-13)**

* Add: view timeline
* Require an explicit login

**0.2.1 (2016-04-13)**

* Fix invalid requirements in setup.py

**0.2.0 (2016-04-12)**

* Bugfixes

**0.1.0 (2016-04-12)**

* Initial release
