# Shell completion

> Introduced in toot 0.40.0

Toot uses [Click shell completion](https://click.palletsprojects.com/en/8.1.x/shell-completion/) which works on Bash, Fish and Zsh.

To enable completion, toot must be [installed](./installation.html) as a command and available by ivoking `toot`. Then follow the instructions for your shell.

**Bash**

Add to `~/.bashrc`:

```
eval "$(_TOOT_COMPLETE=bash_source toot)"
```

**Fish**

Add to `~/.config/fish/completions/toot.fish`:

```
_TOOT_COMPLETE=fish_source toot | source
```

**Zsh**

Add to `~/.zshrc`:

```
eval "$(_TOOT_COMPLETE=zsh_source toot)"
```
