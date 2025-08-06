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

The server should now be live at: http://localhost:3000/

You can view any emails sent by Mastodon at: http://localhost:3000/letter_opener/

## Pleroma

https://docs-develop.pleroma.social/backend/development/setting_up_pleroma_dev/

## Sharkey

Testing toot on [Sharkey](https://activitypub.software/TransFem-org/Sharkey/)

Requires:
* postgresql
* redis
* node + pnpm

```sh
git clone https://activitypub.software/TransFem-org/Sharkey.git
cd Sharkey
git submodule update --init

cp .config/example.yml .config/default.yml
vim .config/default.yml
    # Edit these keys:
    # * db - put in your database credentials
    # * setupPassword - set any password, we'll use "toot"

createdb sharkey
pnpm install --frozen-lockfile
pnpm build
pnpm migrate
pnpm dev
```

Now sharkey should be started. Visit localhost:3000 and create an admin account using `setupPassword` defined in the config file.
