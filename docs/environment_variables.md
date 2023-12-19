# Environment variables

> Introduced in toot v0.40.0

Toot allows setting defaults for parameters via environment variables.

Environment variables should be named `TOOT_<COMMAND_NAME>_<OPTION_NAME>`.

### Examples

Command with option | Environment variable
------------------- | --------------------
`toot --color` | `TOOT_COLOR=true`
`toot --no-color` | `TOOT_COLOR=false`
`toot post --editor vim` | `TOOT_POST_EDITOR=vim`
`toot post --visibility unlisted` | `TOOT_POST_VISIBILITY=unlisted`
`toot tui --media-viewer feh` | `TOOT_TUI_MEDIA_VIEWER=feh`

Note that these can also be set via the [settings file](./settings.html).
