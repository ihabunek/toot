import asyncio
import click
import logging
import os
import random
import sys


from functools import wraps
from typing import List, NamedTuple, Optional, Tuple

from toot import App, User, __version__, config
from toot.asynch import api
from toot.asynch.entities import Account, InstanceV2, Status, from_dict, from_response
from toot.output import echo, print_out
from toot.utils import EOF_KEY, editor_input, multiline_input

# Allow overriding options using environment variables
# https://click.palletsprojects.com/en/8.1.x/options/?highlight=auto_env#values-from-environment-variables

# Tweak the Click context
# https://click.palletsprojects.com/en/8.1.x/api/#context
CONTEXT = dict(
    # Enable using environment variables to set options
    auto_envvar_prefix='TOOT',
    # Add shorthand -h for invoking help
    help_option_names=['-h', '--help'],
    # Give help some more room (default is 80)
    max_content_width=100,
    # Always show default values for options
    show_default=True,
)


def async_command(f):
    # Integrating click with asyncio:
    # https://github.com/pallets/click/issues/85#issuecomment-503464628
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def validate_language(ctx, param, value: str) -> str:
    if value and len(value) != 3:
        raise click.BadParameter(
            "Expected a 3 letter abbreviation according to ISO 639-2 standard."
        )

    return value


# Data object to add to Click context
class Obj(NamedTuple):
    app: Optional[App]
    user: Optional[User]
    color: bool
    debug: bool
    json: bool
    quiet: bool


@click.group(context_settings=CONTEXT)
@click.option("--debug/--no-debug", default=False, help="Log debug info to stderr")
@click.option("--color/--no-color", default=sys.stdout.isatty(), help="Use ANSI color in output")
@click.option("--quiet/--no-quiet", default=False, help="Don't print anything to stdout")
@click.option("--json/--no-json", default=False, help="Print data as JSON rather than human readable textv")
@click.version_option(version=__version__, prog_name="toot")
@click.pass_context
def cli(ctx, debug: bool, color: bool, quiet: bool, json: bool):
    user, app = config.get_active_user_app()
    ctx.color = color
    ctx.obj = Obj(app, user, color, debug, json, quiet)
    if debug:
        logging.basicConfig(level=logging.DEBUG)


@cli.command()
@click.argument("url", required=False)
@click.pass_context
@async_command
async def instance(ctx, url: Optional[str]):
    base_url = url or ctx.obj.app.base_url
    response = await api.instance_v2(base_url)

    if ctx.obj.json:
        click.echo(response.body)
    else:
        instance = from_response(InstanceV2, response)
        click.secho(instance.title, fg="green")
        click.secho(url, fg="blue")
        click.echo(f"Running Mastodon {instance.version}")


@cli.command()
@click.pass_context
@async_command
async def whoami(ctx):
    response = await api.verify_credentials(ctx.obj.app, ctx.obj.user)

    if ctx.obj.json:
        click.echo(response.body)
    else:
        account = from_response(Account, response)
        click.echo(click.style(account.acct, fg="green", bold=True))
        click.echo(click.style(account.display_name, fg="yellow"))
        click.echo(account.note_plaintext)


@cli.command()
@click.pass_context
@async_command
async def timeline(ctx):
    response = await api.timeline(ctx.obj.app, ctx.obj.user)

    if ctx.obj.json:
        click.echo(response.body)
    else:
        timeline = [from_dict(Status, s) for s in response.json()]
        for status in timeline:
            click.echo()
            click.echo(status.original.account.username)
            click.echo(status.original.content)


@cli.command()
@click.argument("text", required=False)
@click.option(
    "-e", "--editor", is_flag=True,
    flag_value=os.environ.get("EDITOR"),
    show_default=os.environ.get("EDITOR"),
    help="""Use an editor to compose your toot, defaults to editor defined in
            the $EDITOR environment variable."""
)
@click.option(
    "-m", "--media", multiple=True,
    help="""Path to a media file to attach (specify multiple times to attach up
            to 4 files)""",
)
@click.option(
    "-d", "--description", multiple=True,
    help="""Plain-text description of the media for accessibility purposes, one
            per attached media""",
)
@click.option(
    "-l", "--language",
    help="ISO 639-2 language code of the toot, to skip automatic detection",
    callback=validate_language
)
def post(
    text: str,
    editor: str,
    media: Tuple[str, ...],
    description: Tuple[str, ...],
    language: Optional[str],
):
    if editor and not sys.stdin.isatty():
        raise click.UsageError("Cannot run editor if not in tty.")

    if media and len(media) > 4:
        raise click.UsageError("Cannot attach more than 4 files.")

    echo("unstyled <red>posting</red> <dim>dim</dim> <underline><red>unde</red><blue>rline</blue></underline> <b>bold</b> unstlyed")
    echo("<bold>Bold<italic> bold and italic </bold>italic</italic>")
    echo("<bold red underline>foo</>bar")
    echo("\\<bold red underline>foo</>bar")
    echo("plain <blue>blue <underline> blue <green>and</green> underline </underline> blue </blue> plain")
    # echo("Done")
    # media_ids = _upload_media(app, user, args)
    # status_text = _get_status_text(text, editor)

    # if not status_text and not media_ids:
    #     raise click.UsageError("You must specify either text or media to post.")

    # response = api.post_status(
    #     app, user, status_text,
    #     visibility=args.visibility,
    #     media_ids=media_ids,
    #     sensitive=args.sensitive,
    #     spoiler_text=args.spoiler_text,
    #     in_reply_to_id=args.reply_to,
    #     language=args.language,
    #     scheduled_at=args.scheduled_at,
    #     content_type=args.content_type
    # )

    # if "scheduled_at" in response:
    #     print_out("Toot scheduled for: <green>{}</green>".format(response["scheduled_at"]))
    # else:
    #     print_out("Toot posted: <green>{}</green>".format(response.get('url')))


def _get_status_text(text, editor):
    isatty = sys.stdin.isatty()

    if not text and not isatty:
        text = sys.stdin.read().rstrip()

    if isatty:
        if editor:
            text = editor_input(editor, text)
        elif not text:
            print_out("Write or paste your toot. Press <yellow>{}</yellow> to post it.".format(EOF_KEY))
            text = multiline_input()

    return text


def _upload_media(app, user, args):
    # Match media to corresponding description and upload
    media = args.media or []
    descriptions = args.description or []
    uploaded_media = []

    for idx, file in enumerate(media):
        description = descriptions[idx].strip() if idx < len(descriptions) else None
        result = _do_upload(app, user, file, description)
        uploaded_media.append(result)

    return [m["id"] for m in uploaded_media]


def _do_upload(app, user, file: str, description: Optional[str]):
    print("Faking upload:", file, description)
    id = random.randint(1, 99999)
    return {"id": id, "text_url": f"http://example.com/{id}"}
