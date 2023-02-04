Toot Async Refactor
===================

Moving to `aiohttp` for full async support + websockets for streaming.

Design goals:

- keep the functional API design
- not coupled with underlying library: requests/aiohttp/httpx
- can easily read returned data decoded from json
- can read returned data without it being decoded (currently not possible)
- can read returned headers
- raises an exception on error
- asynchronous by default, with synchronous variants
- rewrite TUI to use async functions instead of the current callback hell

To think about:

- ability to reuse a aiohttp ClientSession without _having_ to do so. toot's own
  Session object? are there performance issues if a new session is creted each
  time?
- couple app and user into one "context" object to avoid having to pass two
  params for each fn?
- further namespace CLI commands? for example "mute" can be applied to both a
  status and an account, having "toot status mute" and "toot account mute"
  would solve it at expense of verbosity and breaking BC. alternatively, "toot
  mute" could act on a status or account.
- how to implement updating credentials via commandline?
  https://mastodon.example/api/v1/accounts/update_credentials

Unrelated to async refactor:

- how to configure toot? global settings, per-server settings, ...
- is it worth to switch to `click` for CLI, see:
  https://click.palletsprojects.com/en/8.1.x/why/#why-not-argparse

Yak shaving:

- update mastodon template for api methods to include `name="..."` so individual
  API endpoints can be linked in their API docs.
  https://github.com/mastodon/documentation/blob/master/layouts/shortcodes/api-method.html
