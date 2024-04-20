# Running toot tests

## Mastodon

Clone mastodon repo and check out the tag you want to test:

```
git clone https://github.com/mastodon/mastodon
cd mastodon
git checkout v4.2.8
```

Set up the required Ruby version using [ASDF](https://asdf-vm.com/). The
required version is listed in `.ruby-version`.

```
asdf install ruby 3.2.3
asdf local ruby 3.2.3
```

Install and set up database:

```
bundle install
yarn install
rails db:setup
```

Patch code so users are auto-approved:

```
curl https://paste.sr.ht/blob/7c6e08bbacf3da05366b3496b3f24dd03d60bd6d | git am
```

Open registrations:

```
bin/tootctl settings registration open
```

Install foreman to run the thing:

```
gem install foreman
```

Start the server:

```
foreman start
```

## Pleroma

https://docs-develop.pleroma.social/backend/development/setting_up_pleroma_dev/

