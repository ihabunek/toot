import platform
import click
import os
import re
import subprocess
import tempfile
import unicodedata
import warnings

from bs4 import BeautifulSoup
from importlib.metadata import version
from itertools import islice
from typing import Any, Dict, Generator, Iterable, List, Optional, TypeVar
from urllib.parse import urlparse, urlencode, quote, unquote


def str_bool(b: bool) -> str:
    """Convert boolean to string, in the way expected by the API."""
    return "true" if b else "false"


def str_bool_nullable(b: Optional[bool]) -> Optional[str]:
    """Similar to str_bool, but leave None as None"""
    return None if b is None else str_bool(b)


def parse_html(html: str) -> BeautifulSoup:
    # Ignore warnings made by BeautifulSoup, if passed something that looks like
    # a file (e.g. a dot which matches current dict), it will warn that the file
    # should be opened instead of passing a filename.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return BeautifulSoup(html.replace("&apos;", "'"), "html.parser")


def get_text(html: str) -> str:
    """Converts html to text, strips all tags."""
    text = parse_html(html).get_text()
    return unicodedata.normalize("NFKC", text)


def html_to_paragraphs(html: str) -> List[List[str]]:
    """Attempt to convert html to plain text while keeping line breaks.
    Returns a list of paragraphs, each being a list of lines.
    """
    paragraphs = re.split("</?p[^>]*>", html)

    # Convert <br>s to line breaks and remove empty paragraphs
    paragraphs = [re.split("<br */?>", p) for p in paragraphs if p]

    # Convert each line in each paragraph to plain text:
    return [[get_text(line) for line in p] for p in paragraphs]


def format_content(content: str) -> Generator[str, None, None]:
    """Given a Status contents in HTML, converts it into lines of plain text.

    Returns a generator yielding lines of content.
    """

    paragraphs = html_to_paragraphs(content)

    first = True

    for paragraph in paragraphs:
        if not first:
            yield ""

        for line in paragraph:
            yield line

        first = False


EOF_KEY = "Ctrl-Z" if os.name == 'nt' else "Ctrl-D"


def multiline_input() -> str:
    """Lets user input multiple lines of text, terminated by EOF."""
    lines: List[str] = []
    while True:
        try:
            lines.append(input())
        except EOFError:
            break

    return "\n".join(lines).strip()


EDITOR_DIVIDER = "------------------------ >8 ------------------------"

EDITOR_INPUT_INSTRUCTIONS = f"""
{EDITOR_DIVIDER}
Do not modify or remove the line above.
Enter your toot above it.
Everything below it will be ignored.
"""


def editor_input(editor: str, initial_text: str) -> str:
    """Lets user input text using an editor."""
    tmp_path = _tmp_status_path()
    initial_text = (initial_text or "") + EDITOR_INPUT_INSTRUCTIONS

    if not _use_existing_tmp_file(tmp_path):
        with open(tmp_path, "w") as f:
            f.write(initial_text)
            f.flush()

    subprocess.run([editor, tmp_path])

    with open(tmp_path) as f:
        return f.read().split(EDITOR_DIVIDER)[0].strip()


def delete_tmp_status_file() -> None:
    try:
        os.unlink(_tmp_status_path())
    except FileNotFoundError:
        pass


def _tmp_status_path() -> str:
    tmp_dir = tempfile.gettempdir()
    return f"{tmp_dir}/.status.toot"


def _use_existing_tmp_file(tmp_path: str) -> bool:
    if os.path.exists(tmp_path):
        click.echo(f"Found draft status at: {tmp_path}")

        choice = click.Choice(["O", "D"], case_sensitive=False)
        char = click.prompt("Open or Delete?", type=choice, default="O")
        return char == "O"

    return False


def drop_empty_values(data: Dict[Any, Any]) -> Dict[Any, Any]:
    """Remove keys whose values are null"""
    return {k: v for k, v in data.items() if v is not None}


def urlencode_url(url: str) -> str:
    parsed_url = urlparse(url)

    # unencode before encoding, to prevent double-urlencoding
    encoded_path = quote(unquote(parsed_url.path), safe="-._~()'!*:@,;+&=/")
    encoded_query = urlencode({k: quote(unquote(v), safe="-._~()'!*:@,;?/") for k, v in parsed_url.params})
    encoded_url = parsed_url._replace(path=encoded_path, params=encoded_query).geturl()

    return encoded_url


def get_distro_name() -> Optional[str]:
    """Attempt to get linux distro name from platform (requires python 3.10+)"""
    try:
        return platform.freedesktop_os_release()["PRETTY_NAME"]  # type: ignore  # novermin
    except Exception:
        pass


def get_version(name):
    try:
        return version(name)
    except Exception:
        return None


T = TypeVar("T")


def batched(iterable: Iterable[T], n: int) -> Generator[List[T], None, None]:
    """Batch data from the iterable into lists of length n. The last batch may
    be shorter than n."""
    if n < 1:
        raise ValueError("n must be positive")
    iterator = iter(iterable)
    while True:
        batch = list(islice(iterator, n))
        if batch:
            yield batch
        else:
            break
