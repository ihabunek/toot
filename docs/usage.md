Usage
=====

Running `toot` displays a list of available commands.

Running `toot <command> -h` shows the documentation for the given command.

Below is an overview of some common scenarios.

<!-- toc -->

Authentication
--------------

Before tooting, you need to log into a Mastodon instance.

    toot login

You will be redirected to your Mastodon instance to log in and authorize toot to
access your account, and will be given an **authorization code** in return
which you need to enter to log in.

The application and user access tokens will be saved in the configuration file
located at `~/.config/toot/config.json`.

### Using multiple accounts

It's possible to be logged into multiple accounts at the same time. Just
repeat the login process for another instance. You can see all logged in
accounts by running `toot auth`. The currently active account will have an
**ACTIVE** flag next to it.

To switch accounts, use `toot activate`. Alternatively, most commands accept a
`--using` option which can be used to specify the account you wish to use just
that one time.

Finally you can logout from an account by using `toot logout`. This will
remove the stored access tokens for that account.

Post a status
-------------

The simplest action is posting a status.

```sh
toot post "hello there"
```

You can also pipe in the status text:

```sh
echo "Text to post" | toot post
cat post.txt | toot post
toot post < post.txt
```

If no status text is given, you will be prompted to enter some:

```sh
$ toot post
Write or paste your toot. Press Ctrl-D to post it.
```

Finally, you can launch your favourite editor:

```sh
toot post --editor vim
```

Define your editor preference in the `EDITOR` environment variable, then you
don't need to specify it explicitly:

```sh
export EDITOR=vim
toot post --editor
```

### Attachments

You can attach media to your status. Mastodon supports images, video and audio
files. For details on supported formats see
[Mastodon docs on attachments](https://docs.joinmastodon.org/user/posting/#attachments).

It is encouraged to add a plain-text description to the attached media for
accessibility purposes by adding a `--description` option.

To attach an image:

```sh
toot post "hello media" --media path/to/image.png --description "Cool image"
```

You can attach upto 4 attachments by giving multiple `--media` and
`--description` options:

```sh
toot post "hello media" \
  --media path/to/image1.png --description "First image" \
  --media path/to/image2.png --description "Second image" \
  --media path/to/image3.png --description "Third image" \
  --media path/to/image4.png --description "Fourth image"
```

The order of options is not relevant, except that the first given media will be
matched to the first given description and so on.

If the media is sensitive, mark it as such and people will need to click to show
it. This affects all attachments.

```sh
toot post "naughty pics ahoy" --media nsfw.png --sensitive
```

View timeline
-------------

View what's on your home timeline:

```sh
toot timeline
```

Timeline takes various options:

```sh
toot timeline --public          # public timeline
toot timeline --public --local  # public timeline, only this instance
toot timeline --tag photo       # posts tagged with #photo
toot timeline --count 5         # fetch 5 toots (max 20)
toot timeline --once            # don't prompt to fetch more toots
```

Add `--help` to see all the options.

Status actions
--------------

The timeline lists the status ID at the bottom of each toot. Using that status
you can do various actions to it, e.g.:

```sh
toot favourite 123456
toot reblog 123456
```

If it's your own status you can also delete pin or delete it:

```sh
toot pin 123456
toot delete 123456
```

Account actions
---------------

Find a user by their name or account name:

```sh
toot search "name surname"
toot search @someone
toot search someone@someplace.social
```

Once found, follow them:

```sh
toot follow someone@someplace.social
```

If you get bored of them:

```sh
toot mute someone@someplace.social
toot block someone@someplace.social
toot unfollow someone@someplace.social
```
