=====
Usage
=====

Running ``toot`` displays a list of available commands.

Running ``toot <command> -h`` shows the documentation for the given command.

.. code-block:: none

    $ toot

    toot - a Mastodon CLI client

    Authentication:
      toot login       Log into a mastodon instance using your browser (recommended)
      toot login_cli   Log in from the console, does NOT support two factor authentication
      toot activate    Switch between logged in accounts.
      toot logout      Log out, delete stored access keys
      toot auth        Show logged in accounts and instances

    Read:
      toot whoami      Display logged in user details
      toot whois       Display account details
      toot instance    Display instance details
      toot search      Search for users or hashtags
      toot timeline    Show recent items in a timeline (home by default)
      toot curses      An experimental timeline app (doesn't work on Windows)

    Post:
      toot post        Post a status text to your timeline
      toot upload      Upload an image or video file
      toot delete      Delete an existing status

    Accounts:
      toot follow      Follow an account
      toot unfollow    Unfollow an account
      toot mute        Mute an account
      toot unmute      Unmute an account
      toot block       Block an account
      toot unblock     Unblock an account

    To get help for each command run:
      toot <command> --help

    https://github.com/ihabunek/toot

It is possible to pipe status text into `toot post`, for example:

.. code-block:: sh

    echo "Text to post" | toot post
    cat mypost.txt | toot post


Authentication
--------------

Before tooting, you need to login to a Mastodon instance.

.. code-block:: sh

    toot login

You will be redirected to your Mastodon instance to log in and authorize toot to access your account, and will be given an **authorization code** in return which you need to enter to log in.

If you don't use two factor authentication you can also log in directly from the command line:

.. code-block:: sh

    toot login_cli

You will be asked to chose an instance and enter your credentials.

The application and user access tokens will be saved in the configuration file located at ``~/.config/toot/instances/config.json``.

It's possible to be logged into **multiple accounts** at the same time. Just repeat the above process for another instance. You can see all logged in accounts by running ``toot auth``. The currently active account will have an **ACTIVE** flag next to it.

To switch accounts, use ``toot activate``. Alternatively, most commands accept a ``--using`` option which can be used to specify the account you wish to use just that one time.

Finally you can logout from an account by using ``toot logout``. This will remove the stored access tokens for that account.
