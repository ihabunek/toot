Changelog
---------

**0.18.0 (TBA)**

* Add support for public, tag and list timelines in `toot timeline` (#52)
* Add `--sensitive` and `--spoiler-text` options to `toot post` (#63)

**0.17.1 (2018-01-15)**

* Create config folder if it does not exist (#40)
* Fix packaging to include `toot.ui` package (#41)

**0.17.0 (2018-01-15)**

* Changed configuration file format to allow switching between multiple logged
  in accounts (#32)
* Respect XDG_CONFIG_HOME environment variable to locate config home (#12)
* Many improvements to the curses app:
    * Dynamically calculate left window width, supports narrower windows (#27)
    * Redraw windows when terminal size changes (#25)
    * Support scrolling the status list
    * Fetch next batch of statuses when bottom is reached
    * Support up/down arrows (#30)
    * Misc visual improvements

**0.16.2 (2018-01-02)**

* No changes, pushed to fix a packaging issue

**0.16.1 (2017-12-30)**

* Fix bug with app registration

**0.16.0 (2017-12-30)**

* **Drop support for Python 2** because it's a pain to support and caused bugs
  with handling unicode.
* Remove hacky `login_2fa` command, use `login_browser` instead
* Add `instance` command
* Allow `post`ing media without text (#24)

**0.15.1 (2017-12-12)**

* Fix crash when toot's URL is None (#33), thanks @veer66

**0.15.0 (2017-09-09)**

* Fix Windows compatibility (#18)

**0.14.0 (2017-09-07)**

* Add `--debug` option to enable debug logging instead of using the `TOOT_DEBUG`
  environment variable.
* Fix: don't read requirements.txt from setup.py, this fails when packaging deb
  and potentially in some other cases (see #18)

**0.13.0 (2017-08-26)**

* Allow passing `--instance` and `--email` to login command
* Add `login_browser` command for proper two factor authentication through the
  browser (#19, #23)

**0.12.0 (2017-05-08)**

* Add option to disable ANSI color in output (#15)
* Return nonzero error code on error (#14)
* Change license to GPLv3

**0.11.0 (2017-05-07)**

* Fix error when running toot from crontab (#11)
* Minor tweaks

**0.10.0 (2017-04-26)**

* Add commands: `block`, `unblock`, `mute`, `unmute`
* Internal improvements

**0.9.1 (2017-04-24)**

* Fix conflict with curses package name

**0.9.0 (2017-04-21)**

* Add `whois` command
* Add experimental `curses` app for viewing the timeline

**0.8.0 (2017-04-19)**

* Renamed command `2fa` to `login_2fa` **BC BREAK**
* It is now possible to pipe text into `toot post`

**0.7.0 (2017-04-18)**

* Experimental 2FA support (#3)
* Do not create a new application for each login
* **Warning**: Due to changes in configuration format, after upgrading to this
  version, you will be required to log in to your Mastodon instance again.

**0.6.0 (2017-04-17)**

* Add `whoami` command
* Migrate from `optparse` to `argparse`

**0.5.0 (2017-04-16)**

* Add `search`, `follow` and `unfollow` commands
* Migrate from `optparse` to `argparse`

**0.4.0 (2017-04-15)**

* Add `upload` command to post media
* Add `--visibility` and `--media` options to `post` command

**0.3.0 (2017-04-13)**

* Add: view timeline
* Require an explicit login

**0.2.1 (2017-04-13)**

* Fix invalid requirements in setup.py

**0.2.0 (2017-04-12)**

* Bugfixes

**0.1.0 (2017-04-12)**

* Initial release
