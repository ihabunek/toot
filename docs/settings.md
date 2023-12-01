# Settings

Toot can be configured via a [TOML](https://toml.io/en/) settings file.

> Introduced in toot 0.37.0

> **Warning:** Settings are experimental and things may change without warning.

Toot will look for the settings file at:

* `~/.config/toot/settings.toml` (Linux & co.)
* `%APPDATA%\toot\settings.toml` (Windows)

Toot will respect the `XDG_CONFIG_HOME` environement variable if it's set and
look for the settings file in `$XDG_CONFIG_HOME/toot` instead of
`~/.config/toot`.

## Common options

The `[common]` section includes common options which are applied to all commands.

```toml
[common]
# Whether to use ANSI color in output
color = true

# Enable debug logging, shows HTTP requests
debug = true

# Redirect debug log to the given file
debug_file = "/tmp/toot.log"

# Log request and response bodies in the debug log
verbose = false

# Do not write to output
quiet = false
```

## Overriding command defaults

Defaults for command arguments can be override by specifying a `[commands.<name>]` section.

For example, to override `toot post`.

```toml
[commands.post]
editor = "vim"
sensitive = true
visibility = "unlisted"
scheduled_in = "30 minutes"
```

## TUI view images

> Introduced in toot 0.39.0

You can view images in a toot using an external program by setting the
`tui.media_viewer` option to your desired image viewer. When a toot is focused,
pressing `m` will launch the specified executable giving one or more URLs as
arguments. This works well with image viewers like `feh` which accept URLs as
arguments.

```toml
[tui]
media_viewer = "feh"
```

## TUI color palette

TUI uses Urwid which provides several color modes. See
[Urwid documentation](https://urwid.org/manual/displayattributes.html)
for more details.

By default, TUI operates in 16-color mode which can be changed by setting the
`color` setting in the `[tui]` section to one of the following values:

* `1` (monochrome)
* `16` (default)
* `88`
* `256`
* `16777216` (24 bit)

TUI defines a list of colors which can be customized, currently they can be seen
[in the source code](https://github.com/ihabunek/toot/blob/master/toot/tui/constants.py). They can be overriden in the `[tui.palette]` section.

Each color is defined as a list of upto 5 values:

* foreground color (16 color mode)
* background color (16 color mode)
* monochrome color (monochrome mode)
* foreground color (high-color mode)
* background color (high-color mode)

Any colors which are not used by your desired color mode can be skipped or set
to an empty string.

For example, to change the button colors in 16 color mode:

```toml
[tui.palette]
button = ["dark red,bold", ""]
button_focused = ["light gray", "green"]
```

In monochrome mode:

```toml
[tui]
colors = 1

[tui.palette]
button = ["", "", "bold"]
button_focused = ["", "", "italics"]
```

In 256 color mode:

```toml
[tui]
colors = 256

[tui.palette]
button = ["", "", "", "#aaa", "#bbb"]
button_focused = ["", "", "", "#aaa", "#bbb"]
```
