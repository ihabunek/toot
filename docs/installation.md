Installation
============

## Package repositories

toot is packaged for various platforms. If possible use your OS's package manager to install toot.

<details>
    <summary>Packaging status</summary>
    <a href="https://repology.org/project/toot/versions" style="display: block; margin-top: 2rem">
        <img src="https://repology.org/badge/vertical-allrepos/toot.svg?columns=4" alt="Packaging status" />
    </a>
</details>

## Homebrew

For Mac users, toot is available [in homebrew](https://formulae.brew.sh/formula/toot#default).

    brew install toot

## Using pipx

pipx installs packages from PyPI into isolated environments. It is the
recommended installation method if there is no OS package or the package is
outdated.

Firstly, install pipx following their [installation instructions](https://pipx.pypa.io/stable/installation/).

Install toot:

    pipx install toot

Install with optional image support:

    pipx install "toot[images]"

Upgrade to latest version:

    pipx upgrade toot

## From source

You can get the latest source distribution [from Github](https://github.com/ihabunek/toot/releases/latest/).

Clone the project and install into a virtual environment.

```
git clone git@github.com:ihabunek/toot.git
cd toot
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

After this, the executable is available at `.venv/bin/toot`.

To install with optonal image support:

```
pip install ".[images]"
```