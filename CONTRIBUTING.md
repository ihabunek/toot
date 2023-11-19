Toot contribution guide
=======================

Firstly, thank you for contributing to toot!

Relevant links which will be referenced below:

* [toot documentation](https://toot.bezdomni.net/)
* [toot-discuss mailing list](https://lists.sr.ht/~ihabunek/toot-discuss)
  used for discussion as well as accepting patches
* [toot project on github](https://github.com/ihabunek/toot)
  here you can report issues and submit pull requests
* #toot IRC channel on [libera.chat](https://libera.chat)

## Code of conduct

Please be kind and patient. Toot is governed by one human with a full time job.

## I have a question

First, check if your question is addressed in the documentation or the mailing
list. If not, feel free to send an email to the mailing list. You may want to
subscribe to the mailing list to receive replies.

Alternatively, you can ask your question on the IRC channel and ping me
(ihabunek). You may have to wait for a response, please be patient.

Please don't open Github issues for questions.

## I want to contribute

### Reporting a bug

First check you're using the
[latest version](https://github.com/ihabunek/toot/releases/) of toot and verify
the bug is present in this version.

Search Github issues to check the bug hasn't already been reported.

To report a bug open an
[issue on Github](https://github.com/ihabunek/toot/issues) or send an
email to the [mailing list](https://lists.sr.ht/~ihabunek/toot-discuss).

* Run `toot env` and include its contents in the bug report.
* Explain the behavior you would expect and the actual behavior.
* Please provide as much context as possible and describe the reproduction steps
  that someone else can follow to recreate the issue on their own.

### Suggesting enhancements

This includes suggesting new features or changes to existing ones.

Search Github issues to check the enhancement has not already been requested. If
it hasn't, [open a new issue](https://github.com/ihabunek/toot/issues).

Your request will be reviewed to see if it's a good fit for toot. Implementing
requested features depends on the available time and energy of the maintainer
and other contributors. Be patient.

### Contributing code

When contributing to toot, please only submit code that you have authored or
code whose license allows it to be included in toot. You agree that the code
you submit will be published under the [toot license](LICENSE).

#### Setting up a dev environment

Check out toot (or a fork) and install it into a virtual environment.

```
git clone git@github.com:ihabunek/toot.git
cd toot
python3 -m venv _env
source _env/bin/activate
pip install --editable .
pip install -r requirements-dev.txt
pip install -r requirements-test.txt
```

While the virtual env is active, you can run `./_env/bin/toot` to
execute the one you checked out. This allows you to make changes and
test them.

#### Crafting good commits

Please put some effort into breaking your contribution up into a series of well
formed commits. If you're unsure what this means, there is a good guide
available at https://cbea.ms/git-commit/.

Rules for commits:

* each commit should ideally contain only one change
* don't bundle multiple unrelated changes into a single commit
* write descriptive and well formatted commit messages

Rules for commit messages:

* separate subject from body with a blank line
* limit the subject line to 50 characters
* capitalize the subject line
* do not end the subject line with a period
* use the imperative mood in the subject line
* wrap the body at 72 characters
* use the body to explain what and why vs. how

For a more detailed explanation with examples see the guide at
https://cbea.ms/git-commit/

If you use vim to write your commit messages, it will already enforce some of
these rules for you.

#### Run tests before submitting

You can run code and sytle tests by running:

```
make test
```

This runs three tools:

* `pytest` runs the test suite
* `flake8` checks code formatting
* `vermin` checks that minimum python version

Please ensure all three commands succeed before submitting your patches.

#### Submitting patches

To submit your code either open
[a pull request](https://github.com/ihabunek/toot/pulls) on Github, or send
patch(es) to [the mailing list](https://lists.sr.ht/~ihabunek/toot-discuss).

If sending to the mailing list, patches should be sent using `git send-email`.
If you're unsure how to do this, there is a good guide at
https://git-send-email.io/.

---

Parts of this guide were taken from the following sources:

* https://contributing.md/
* https://cbea.ms/git-commit/
