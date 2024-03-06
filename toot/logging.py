import json
import sys

from logging import getLogger
from requests import Request, RequestException, Response
from urllib.parse import urlencode

logger = getLogger("toot")

VERBOSE = "--verbose" in sys.argv


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


def log_request(request: Request):
    logger.debug(f" --> {request.method} {_url(request)}")

    if VERBOSE and request.headers:
        headers = censor_secrets(request.headers)
        logger.debug(f" --> HEADERS: {headers}")

    if VERBOSE and request.data:
        data = truncate(request.data)
        logger.debug(f" --> DATA:    {data}")

    if VERBOSE and request.json:
        data = truncate(json.dumps(request.json))
        logger.debug(f" --> JSON:    {data}")

    if VERBOSE and request.files:
        logger.debug(f" --> FILES:   {request.files}")


def log_response(response: Response):
    method = response.request.method
    url = response.request.url
    elapsed = response.elapsed.microseconds // 1000
    logger.debug(f" <-- {method} {url} HTTP {response.status_code} {elapsed}ms")

    if VERBOSE and response.content:
        content = truncate(response.content.decode())
        logger.debug(f" <-- {content}")


def log_request_exception(request: Request, ex: RequestException):
    logger.debug(f" <-- {request.method} {_url(request)} Exception: {ex}")


def _url(request):
    url = request.url
    if request.params:
        url += f"?{urlencode(request.params)}"
    return url
