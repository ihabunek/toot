Toot - a Mastodon CLI client
============================

![](https://raw.githubusercontent.com/ihabunek/toot/master/trumpet.png)

Toot is a CLI and TUI tool for interacting with Mastodon instances from the command line.

[![](https://img.shields.io/badge/author-%40ihabunek-blue.svg?maxAge=3600&style=flat-square)](https://mastodon.social/@ihabunek)
[![](https://img.shields.io/github/license/ihabunek/toot.svg?maxAge=3600&style=flat-square)](https://opensource.org/licenses/GPL-3.0)
[![](https://img.shields.io/pypi/v/toot.svg?maxAge=3600&style=flat-square)](https://pypi.python.org/pypi/toot)

## Resources

* Installation instructions: https://toot.bezdomni.net/installation.html
* Homepage: https://github.com/ihabunek/toot
* Issues: https://github.com/ihabunek/toot/issues
* Documentation: https://toot.bezdomni.net/
* Mailing list for discussion, support and patches:
  https://lists.sr.ht/~ihabunek/toot-discuss
* Informal discussion: `#toot` IRC channel on [libera.chat](https://libera.chat/)

## Features

* Posting, replying, deleting statuses
* Support for media uploads, spoiler text, sensitive content
* Search statused, accounts, hashtags
* Following, muting and blocking accounts
* Simple switching between authenticated in Mastodon accounts

## Quick start

Explore the command line interface:
* `toot --help` - show available commands
* `toot <command> --help` - show documentation for `<command>`

Log in with your account:

```sh
toot login
```
Post a status:

```sh
toot post "Hello, World!"
```

View your home timeline:

```sh
toot timelines home
````

See more usage examples in the [documentation](https://toot.bezdomni.net/usage.html).

## Terminal User Interface

Toot terminal user interface (`toot tui`) is no longer being developed.

Instead check out [tooi](https://codeberg.org/ihabunek/tooi) which is a more
fully featured Mastodon TUI.

## License

Copyright Ivan Habunek <ivan@habunek.com> and contributors.

Licensed under [GPLv3](http://www.gnu.org/licenses/gpl-3.0.html), see [LICENSE](LICENSE).
