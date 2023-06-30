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

Defaults for command arguments can be override by specifying a `[command.<name>]` section.

For example, to override `toot post`.

```toml
[command.post]
editor = "vim"
sensitive = true
visibility = "unlisted"
scheduled_in = "30 minutes"
```
