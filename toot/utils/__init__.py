import os
import re
import socket
import subprocess
import tempfile
import unicodedata
import warnings

from bs4 import BeautifulSoup
from typing import Dict

from toot.exceptions import ConsoleError
from urllib.parse import urlparse, urlencode, quote, unquote


def str_bool(b):
    """Convert boolean to string, in the way expected by the API."""
    return "true" if b else "false"


def str_bool_nullable(b):
    """Similar to str_bool, but leave None as None"""
    return None if b is None else str_bool(b)


def parse_html(html: str) -> BeautifulSoup:
    # Ignore warnings made by BeautifulSoup, if passed something that looks like
    # a file (e.g. a dot which matches current dict), it will warn that the file
    # should be opened instead of passing a filename.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return BeautifulSoup(html.replace("&apos;", "'"), "html.parser")


def get_text(html):
    """Converts html to text, strips all tags."""
    text = parse_html(html).get_text()
    return unicodedata.normalize("NFKC", text)


def html_to_paragraphs(html):
    """Attempt to convert html to plain text while keeping line breaks.
    Returns a list of paragraphs, each being a list of lines.
    """
    paragraphs = re.split("</?p[^>]*>", html)

    # Convert <br>s to line breaks and remove empty paragraphs
    paragraphs = [re.split("<br */?>", p) for p in paragraphs if p]

    # Convert each line in each paragraph to plain text:
    return [[get_text(line) for line in p] for p in paragraphs]


def format_content(content):
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


def domain_exists(name):
    try:
        socket.gethostbyname(name)
        return True
    except OSError:
        return False


def assert_domain_exists(domain):
    if not domain_exists(domain):
        raise ConsoleError("Domain {} not found".format(domain))


EOF_KEY = "Ctrl-Z" if os.name == 'nt' else "Ctrl-D"


def multiline_input():
    """Lets user input multiple lines of text, terminated by EOF."""
    lines = []
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


def editor_input(editor: str, initial_text: str):
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


def read_char(values, default):
    values = [v.lower() for v in values]

    while True:
        value = input().lower()
        if value == "":
            return default
        if value in values:
            return value


def delete_tmp_status_file():
    try:
        os.unlink(_tmp_status_path())
    except FileNotFoundError:
        pass


def _tmp_status_path() -> str:
    tmp_dir = tempfile.gettempdir()
    return f"{tmp_dir}/.status.toot"


def _use_existing_tmp_file(tmp_path) -> bool:
    from toot.output import print_out

    if os.path.exists(tmp_path):
        print_out(f"<cyan>Found a draft status at: {tmp_path}</cyan>")
        print_out("<cyan>[O]pen (default) or [D]elete?</cyan> ", end="")
        char = read_char(["o", "d"], "o")
        return char == "o"

    return False


def drop_empty_values(data: Dict) -> Dict:
    """Remove keys whose values are null"""
    return {k: v for k, v in data.items() if v is not None}


def args_get_instance(instance, scheme, default=None):
    if not instance:
        return default

    if scheme == "http":
        _warn_scheme_deprecated()

    if instance.startswith("http"):
        return instance.rstrip("/")
    else:
        return f"{scheme}://{instance}"


def _warn_scheme_deprecated():
    from toot.output import print_err

    print_err("\n".join([
        "--disable-https flag is deprecated and will be removed.",
        "Please specify the instance as URL instead.",
        "e.g. instead of writing:",
        "  toot instance unsafehost.com --disable-https",
        "instead write:",
        "  toot instance http://unsafehost.com\n"
    ]))


def urlencode_url(url):
    parsed_url = urlparse(url)

    # unencode before encoding, to prevent double-urlencoding
    encoded_path = quote(unquote(parsed_url.path), safe="-._~()'!*:@,;+&=/")
    encoded_query = urlencode({k: quote(unquote(v), safe="-._~()'!*:@,;?/") for k, v in parsed_url.params})
    encoded_url = parsed_url._replace(path=encoded_path, params=encoded_query).geturl()

    return encoded_url
