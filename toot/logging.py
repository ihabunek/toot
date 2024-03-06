import json
import sys

from logging import getLogger

logger = getLogger('toot')

VERBOSE = "--verbose" in sys.argv
COLOR = "--no-color" not in sys.argv

if COLOR:
    ANSI_RED = "\033[31m"
    ANSI_GREEN = "\033[32m"
    ANSI_YELLOW = "\033[33m"
    ANSI_END_COLOR = "\033[0m"
else:
    ANSI_RED = ""
    ANSI_GREEN = ""
    ANSI_YELLOW = ""
    ANSI_END_COLOR = ""


def censor_secrets(headers):
    def _censor(k, v):
        if k == "Authorization":
            return (k, "***CENSORED***")
        return k, v

    return {_censor(k, v) for k, v in headers.items()}


def truncate(line):
    if not VERBOSE and len(line) > 100:
        return line[:100] + "…"

    return line


def log_request(request):

    logger.debug(f">>> {ANSI_GREEN}{request.method} {request.url}{ANSI_END_COLOR}")

    if request.headers:
        headers = censor_secrets(request.headers)
        logger.debug(f">>> HEADERS: {ANSI_GREEN}{headers}{ANSI_END_COLOR}")

    if request.data:
        data = truncate(request.data)
        logger.debug(f">>> DATA:    {ANSI_GREEN}{data}{ANSI_END_COLOR}")

    if request.json:
        data = truncate(json.dumps(request.json))
        logger.debug(f">>> JSON:    {ANSI_GREEN}{data}{ANSI_END_COLOR}")

    if request.files:
        logger.debug(f">>> FILES:   {ANSI_GREEN}{request.files}{ANSI_END_COLOR}")

    if request.params:
        logger.debug(f">>> PARAMS:  {ANSI_GREEN}{request.params}{ANSI_END_COLOR}")


def log_response(response):

    content = truncate(response.content.decode())

    if response.ok:
        logger.debug(f"<<< {ANSI_GREEN}{response}{ANSI_END_COLOR}")
        logger.debug(f"<<< {ANSI_YELLOW}{content}{ANSI_END_COLOR}")
    else:
        logger.debug(f"<<< {ANSI_RED}{response}{ANSI_END_COLOR}")
        logger.debug(f"<<< {ANSI_RED}{content}{ANSI_END_COLOR}")


def log_debug(*msgs):
    logger.debug(" ".join(str(m) for m in msgs))
