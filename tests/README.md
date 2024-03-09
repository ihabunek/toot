Testing toot
============

This document is WIP.

Mastodon
--------

TODO

Pleroma
-------

TODO

Akkoma
------

Install using the guide here:
https://docs.akkoma.dev/stable/installation/docker_en/

Disable captcha and throttling by adding this to `config/prod.exs`:

```ex
# Disable captcha for testing
config :pleroma, Pleroma.Captcha,
  enabled: false

# Disable rate limiting for testing
config :pleroma, :rate_limit,
  authentication: nil,
  timeline: nil,
  search: nil,
  app_account_creation: nil,
  relations_actions: nil,
  relation_id_action: nil,
  statuses_actions: nil,
  status_id_action: nil,
  password_reset: nil,
  account_confirmation_resend: nil,
  ap_routes: nil
```
