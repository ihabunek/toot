=====
Usage
=====

Running ``toot`` displays a list of available commands.

Running ``toot <command> -h`` shows the documentation for the given command.

.. code-block:: none

    $ toot

    toot - a Mastodon CLI client
    v0.27.0

    Authentication:
      toot login           Log into a mastodon instance using your browser (recommended)
      toot login_cli       Log in from the console, does NOT support two factor authentication
      toot activate        Switch between logged in accounts.
      toot logout          Log out, delete stored access keys
      toot auth            Show logged in accounts and instances

    TUI:
      toot tui             Launches the toot terminal user interface

    Read:
      toot whoami          Display logged in user details
      toot whois           Display account details
      toot notifications   Notifications for logged in user
      toot instance        Display instance details
      toot search          Search for users or hashtags
      toot thread          Show toot thread items
      toot timeline        Show recent items in a timeline (home by default)

    Post:
      toot post            Post a status text to your timeline
      toot upload          Upload an image or video file

    Status:
      toot delete          Delete a status
      toot favourite       Favourite a status
      toot unfavourite     Unfavourite a status
      toot reblog          Reblog a status
      toot unreblog        Unreblog a status
      toot reblogged_by    Show accounts that reblogged the status
      toot pin             Pin a status
      toot unpin           Unpin a status

    Accounts:
      toot follow          Follow an account
      toot unfollow        Unfollow an account
      toot mute            Mute an account
      toot unmute          Unmute an account
      toot block           Block an account
      toot unblock         Unblock an account

    To get help for each command run:
      toot <command> --help

    https://github.com/ihabunek/toot


Authentication
--------------

Before tooting, you need to log into a Mastodon instance.

.. code-block:: sh

    toot login

You will be redirected to your Mastodon instance to log in and authorize toot to
access your account, and will be given an **authorization code** in return which
you need to enter to log in.

The application and user access tokens will be saved in the configuration file
located at ``~/.config/toot/config.json``.

Using multiple accounts
~~~~~~~~~~~~~~~~~~~~~~~

It's possible to be logged into **multiple accounts** at the same time. Just
repeat the login process for another instance. You can see all logged in
accounts by running ``toot auth``. The currently active account will have an
**ACTIVE** flag next to it.

To switch accounts, use ``toot activate``. Alternatively, most commands accept a
``--using`` option which can be used to specify the account you wish to use just
that one time.

Finally you can logout from an account by using ``toot logout``. This will
remove the stored access tokens for that account.

Post a status
-------------

The simplest action is posting a status.

.. code-block:: bash

  toot post "hello there"

You can also pipe in the status text:

.. code-block:: bash

  echo "Text to post" | toot post
  cat post.txt | toot post
  toot post < post.txt

If no status text is given, you will be prompted to enter some:

.. code-block:: bash

  $ toot post
  Write or paste your toot. Press Ctrl-D to post it.

Finally, you can launch your favourite editor:

.. code-block:: bash

  toot post --editor vim

Define your editor preference in the ``EDITOR`` environment variable, then you
don't need to specify it explicitly:

.. code-block:: bash

  export EDITOR=vim
  toot post --editor

Attachments
~~~~~~~~~~~

You can attach media to your status. Mastodon supports images, video and audio
files. For details on supported formats see `Mastodon docs on attachments
<https://docs.joinmastodon.org/user/posting/#attachments>`_.

It is encouraged to add a plain-text description to the attached media for
accessibility purposes by adding a ``--description`` option.

To attach an image:

.. code-block:: bash

  toot post "hello media" --media path/to/image.png --description "Cool image"

You can attach upto 4 attachments by giving multiple ``--media`` and
``--description`` options:

.. code-block:: bash

  toot post "hello media" \
    --media path/to/image1.png --description "First image" \
    --media path/to/image2.png --description "Second image" \
    --media path/to/image3.png --description "Third image" \
    --media path/to/image4.png --description "Fourth image"

The order of options is not relevant, except that the first given media will be
matched to the first given description and so on.

If the media is sensitive, mark it as such and people will need to click to show
it. This affects all attachments.

.. code-block:: bash

  toot post "naughty pics ahoy" --media nsfw.png --sensitive

View timeline
-------------

View what's on your home timeline:

.. code-block:: bash

  toot timeline

Timeline takes various options:

.. code-block:: bash

  toot timeline --public          # public timeline
  toot timeline --public --local  # public timeline, only this instance
  toot timeline --tag photo       # posts tagged with #photo
  toot timeline --count 5         # fetch 5 toots (max 20)
  toot timeline --once            # don't prompt to fetch more toots

Status actions
--------------

The timeline lists the status ID at the bottom of each toot. Using that status
you can do various actions to it, e.g.:

.. code-block:: bash

  toot favourite 123456
  toot reblog 123456

If it's your own status you can also delete pin or delete it:

.. code-block:: bash

  toot pin 123456
  toot delete 123456

Account actions
---------------

Find a user by their name or account name:

.. code-block:: bash

  toot search "name surname"
  toot search @someone
  toot search someone@someplace.social

Once found, follow them:

.. code-block:: bash

  toot follow someone@someplace.social

If you get bored of them:

.. code-block:: bash

  toot mute someone@someplace.social
  toot block someone@someplace.social
  toot unfollow someone@someplace.social

Using the Curses UI
-------------------

toot has a curses-based terminal user interface. The command to start it is ``toot tui``.

To navigate the UI use these commands:

* ``k`` or ``up arrow`` to move up the list of tweets
* ``j`` or ``down arrow`` to move down the list of tweets
* ``h`` to show a help screen
* ``t`` to view status thread
* ``v`` to view the current toot in a browser
* ``b`` to boost or unboost a status
* ``f`` to favourite or unfavourite a status
* ``q`` to quit the curses interface and return to the command line
* ``s`` to show sensitive content. (This is per-toot, and there will be a read bar in the toot to indicate that it is there.)

*Note that the curses UI is not available on Windows.*
