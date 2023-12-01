Advanced usage
==============

Disabling HTTPS
---------------

You may pass the `--disable-https` flag to use unencrypted HTTP instead of
HTTPS for a given instance. This is inherently insecure and should be used only
when connecting to local development instances.

```sh
toot login --disable-https --instance localhost:8080
```

Using proxies
-------------

You can configure proxies by setting the `HTTPS_PROXY` or `HTTP_PROXY`
environment variables. This will cause all http(s) requests to be proxied
through the specified server.

For example:

```sh
export HTTPS_PROXY="http://1.2.3.4:5678"
toot login --instance mastodon.social
```

**NB:** This feature is provided by
[requests](http://docs.python-requests.org/en/master/user/advanced/#proxies>)
and setting the environment variable will affect other programs using this
library.

This environment can be set for a single call to toot by prefixing the command
with the environment variable:

```
HTTPS_PROXY="http://1.2.3.4:5678" toot login --instance mastodon.social
```
