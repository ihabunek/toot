import click
import re
import shutil
import textwrap
import typing as t

from toot.entities import Account, Data, Instance, Notification, Poll, Status, List
from toot.utils import get_text, html_to_paragraphs
from toot.wcstring import wc_wrap
from wcwidth import wcswidth


DEFAULT_WIDTH = 80


def get_max_width() -> int:
    return click.get_current_context().max_content_width or DEFAULT_WIDTH


def get_terminal_width() -> int:
    return shutil.get_terminal_size().columns


def get_width() -> int:
    return min(get_terminal_width(), get_max_width())


def print_warning(text: str):
    click.secho(f"Warning: {text}", fg="yellow", err=True)


def print_instance(instance: Instance):
    width = get_width()
    click.echo(instance_to_text(instance, width))


def instance_to_text(instance: Instance, width: int) -> str:
    return "\n".join(instance_lines(instance, width))


def instance_lines(instance: Instance, width: int) -> t.Generator[str, None, None]:
    yield f"{green(instance.title)}"
    yield f"{blue(instance.uri)}"
    yield f"running Mastodon {instance.version}"
    yield ""

    if instance.description:
        for paragraph in re.split(r"[\r\n]+", instance.description.strip()):
            paragraph = get_text(paragraph)
            yield textwrap.fill(paragraph, width=width)
            yield ""

    if instance.rules:
        yield "Rules:"
        for ordinal, rule in enumerate(instance.rules):
            ordinal = f"{ordinal + 1}."
            lines = textwrap.wrap(rule.text, width - len(ordinal))
            first = True
            for line in lines:
                if first:
                    yield f"{ordinal} {line}"
                    first = False
                else:
                    yield f"{' ' * len(ordinal)} {line}"
        yield ""

    contact = instance.contact_account
    if contact:
        yield f"Contact: {contact.display_name} @{contact.acct}"


def print_account(account: Account) -> None:
    width = get_width()
    click.echo(account_to_text(account, width))


def account_to_text(account: Account, width: int) -> str:
    return "\n".join(account_lines(account, width))


def account_lines(account: Account, width: int) -> t.Generator[str, None, None]:
    acct = f"@{account.acct}"
    since = account.created_at.strftime("%Y-%m-%d")

    yield f"{green(acct)} {account.display_name}"

    if account.note:
        yield ""
        yield from html_lines(account.note, width)

    yield ""
    yield f"ID: {green(account.id)}"
    yield f"Since: {green(since)}"
    yield ""
    yield f"Followers: {yellow(account.followers_count)}"
    yield f"Following: {yellow(account.following_count)}"
    yield f"Statuses: {yellow(account.statuses_count)}"

    if account.fields:
        for field in account.fields:
            name = field.name.title()
            yield f'\n{yellow(name)}:'
            yield from html_lines(field.value, width)
            if field.verified_at:
                yield green("✓ Verified")

    yield ""
    yield account.url


def print_acct_list(accounts):
    for account in accounts:
        acct = green(f"@{account['acct']}")
        click.echo(f"* {acct} {account['display_name']}")


def print_tag_list(tags):
    for tag in tags:
        click.echo(f"* {format_tag_name(tag)}\t{tag['url']}")


def print_lists(lists: t.List[List]):
    headers = ["ID", "Title", "Replies"]
    data = [[lst.id, lst.title, lst.replies_policy or ""] for lst in lists]
    print_table(headers, data)


def print_table(headers: t.List[str], data: t.List[t.List[str]]):
    widths = [[len(cell) for cell in row] for row in data + [headers]]
    widths = [max(width) for width in zip(*widths)]

    def print_row(row):
        for idx, cell in enumerate(row):
            width = widths[idx]
            click.echo(cell.ljust(width), nl=False)
            click.echo("  ", nl=False)
        click.echo()

    underlines = ["-" * width for width in widths]

    print_row(headers)
    print_row(underlines)

    for row in data:
        print_row(row)


def print_list_accounts(accounts):
    if accounts:
        click.echo("Accounts in list:\n")
        print_acct_list(accounts)
    else:
        click.echo("This list has no accounts.")


def print_search_results(results):
    accounts = results["accounts"]
    hashtags = results["hashtags"]

    if accounts:
        click.echo("\nAccounts:")
        print_acct_list(accounts)

    if hashtags:
        click.echo("\nHashtags:")
        click.echo(", ".join([format_tag_name(tag) for tag in hashtags]))

    if not accounts and not hashtags:
        click.echo("Nothing found")


def print_status(status: Status) -> None:
    width = get_width()
    click.echo(status_to_text(status, width))


def status_to_text(status: Status, width: int) -> str:
    return "\n".join(status_lines(status))


def status_lines(status: Status) -> t.Generator[str, None, None]:
    width = get_width()
    status_id = status.id
    in_reply_to_id = status.in_reply_to_id
    reblogged_by = status.account if status.reblog else None
    status = status.original

    time = status.created_at.strftime('%Y-%m-%d %H:%M %Z')
    username = "@" + status.account.acct
    spacing = width - wcswidth(username) - wcswidth(time) - 2

    display_name = status.account.display_name

    if display_name:
        author = f"{green(display_name)} {blue(username)}"
        spacing -= wcswidth(display_name) + 1
    else:
        author = blue(username)

    spaces = " " * spacing
    yield f"{author} {spaces} {yellow(time)}"

    yield ""
    yield from html_lines(status.content, width)

    if status.media_attachments:
        yield ""
        yield "Media:"
        for attachment in status.media_attachments:
            url = attachment.url
            for line in wc_wrap(url, width):
                yield line

    if status.poll:
        yield from poll_lines(status.poll)

    reblogged_by_acct = f"@{reblogged_by.acct}" if reblogged_by else None
    yield ""

    reply = f"↲ In reply to {yellow(in_reply_to_id)} " if in_reply_to_id else ""
    boost = f"↻ {blue(reblogged_by_acct)} boosted " if reblogged_by else ""
    yield f"ID {yellow(status_id)}  Visibility: {status.visibility}  {reply} {boost}"


def html_lines(html: str, width: int) -> t.Generator[str, None, None]:
    first = True
    for paragraph in html_to_paragraphs(html):
        if not first:
            yield ""
        for line in paragraph:
            for subline in wc_wrap(line, width):
                yield subline
        first = False


def poll_lines(poll: Poll) -> t.Generator[str, None, None]:
    for idx, option in enumerate(poll.options):
        perc = (round(100 * option.votes_count / poll.votes_count)
            if poll.votes_count and option.votes_count is not None else 0)

        if poll.voted and poll.own_votes and idx in poll.own_votes:
            voted_for = yellow(" ✓")
        else:
            voted_for = ""

        yield f"{option.title} - {perc}% {voted_for}"

    poll_footer = f'Poll · {poll.votes_count} votes'

    if poll.expired:
        poll_footer += " · Closed"

    if poll.expires_at:
        expires_at = poll.expires_at.strftime("%Y-%m-%d %H:%M")
        poll_footer += f" · Closes on {expires_at}"

    yield ""
    yield poll_footer


def print_timeline(items: t.Iterable[Status]):
    print_divider()
    for item in items:
        print_status(item)
        print_divider()


def print_notification(notification: Notification):
    print_notification_header(notification)
    if notification.status:
        print_divider(char="-")
        print_status(notification.status)


def print_notifications(notifications: t.List[Notification]):
    for notification in notifications:
        if notification.type not in ['pleroma:emoji_reaction']:
            print_divider()
            print_notification(notification)
    print_divider()


def print_notification_header(notification: Notification):
    account_name = format_account_name(notification.account)

    if (notification.type == "follow"):
        click.echo(f"{account_name} now follows you")
    elif (notification.type == "mention"):
        click.echo(f"{account_name} mentioned you")
    elif (notification.type == "reblog"):
        click.echo(f"{account_name} reblogged your status")
    elif (notification.type == "favourite"):
        click.echo(f"{account_name} favourited your status")
    elif (notification.type == "update"):
        click.echo(f"{account_name} edited a post")
    else:
        click.secho(f"Unknown notification type: '{notification.type}'", err=True, fg="yellow")
        click.secho("Please report an issue to toot.", err=True, fg="yellow")


def print_divider(char: str = "─"):
    click.echo(char * get_width())


def format_tag_name(tag):
    return green(f"#{tag['name']}")


def format_account_name(account: Account) -> str:
    acct = blue(f"@{account.acct}")
    if account.display_name:
        return f"{green(account.display_name)} {acct}"
    else:
        return acct


def print_diags(instance_dict: t.Optional[Data], include_files: bool):
    from importlib.metadata import version

    click.echo(f'{green("Diagnostic Information")}')
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    click.echo(f'{green("Current Date/Time:")} {now.strftime("%Y-%m-%d %H:%M:%S %Z")}')

    from toot import __version__, config, settings
    click.echo(f'{green("Toot version:")} {__version__}')

    import platform
    click.echo(f'{green("Platform:")} {platform.platform()}')

    # print distro - only call if available (python 3.10+)
    fd_os_release = getattr(platform, "freedesktop_os_release", None)  # novermin
    if callable(fd_os_release):  # novermin
        try:
            name = platform.freedesktop_os_release()['PRETTY_NAME']
            click.echo(f'{green("Distro:")} {name}')
        except:  # noqa
            pass

    click.echo(f'{green("Python version:")} {platform.python_version()}')
    click.echo(green("Dependency versions:"))

    deps = sorted(['beautifulsoup4', 'click', 'requests', 'tomlkit', 'urwid', 'wcwidth',
            'pillow', 'term-image', 'urwidgets', 'flake8', 'pytest', 'setuptools',
            'vermin', 'typing-extensions'])

    for dep in deps:
        try:
            ver = version(dep)
        except:  # noqa
            ver = yellow("not installed")

        click.echo(f"\t{dep}: {ver}")

    click.echo(f'{green("Settings file path:")} {settings.get_settings_path()}')
    click.echo(f'{green("Config file path:")} {config.get_config_file_path()}')

    if instance_dict:
        try:
            click.echo(f'{green("Server URI:")} {instance_dict["uri"]}')
        except:  # noqa E722
            pass
        try:
            click.echo(f'{green("Server version:")} {instance_dict["version"]}')
        except:  # noqa E722
            pass

    if include_files:
        click.echo(f'{green("Settings file contents:")}')
        try:
            with open(settings.get_settings_path(), 'r') as f:
                print(f.read())
        except:  # noqa
            click.echo(f'{yellow("Could not open settings file")}')

            click.echo('')

        click.echo(f'{green("Config file contents:")}')
        try:
            with open(config.get_config_file_path(), 'r') as f:
                for line in f:
                    # Do not output client secret or access token lines
                    if "client_" in line or "token" in line:
                        click.echo(f'{yellow("***CONTENTS REDACTED***")}')
                    else:
                        click.echo(line, nl=False)

        except:  # noqa
            click.echo(f'{yellow("Could not open config file")}')

        click.echo('')


# Shorthand functions for coloring output

def blue(text: t.Any) -> str:
    return click.style(text, fg="blue")


def bold(text: t.Any) -> str:
    return click.style(text, bold=True)


def cyan(text: t.Any) -> str:
    return click.style(text, fg="cyan")


def dim(text: t.Any) -> str:
    return click.style(text, dim=True)


def green(text: t.Any) -> str:
    return click.style(text, fg="green")


def yellow(text: t.Any) -> str:
    return click.style(text, fg="yellow")
