import json
import sys

from logging import getLogger

logger = getLogger('toot')

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


def log_request(request):
    logger.debug(">>> \033[32m{} {}\033[0m".format(request.method, request.url))

    if request.headers:
        headers = censor_secrets(request.headers)
        logger.debug(">>> HEADERS: \033[33m{}\033[0m".format(headers))

    if request.data:
        data = truncate(request.data)
        logger.debug(">>> DATA:    \033[33m{}\033[0m".format(data))

    if request.json:
        data = truncate(json.dumps(request.json))
        logger.debug(">>> JSON:    \033[33m{}\033[0m".format(data))

    if request.files:
        logger.debug(">>> FILES:   \033[33m{}\033[0m".format(request.files))

    if request.params:
        logger.debug(">>> PARAMS:  \033[33m{}\033[0m".format(request.params))


def log_response(response):
    content = truncate(response.content.decode())

    if response.ok:
        logger.debug("<<< \033[32m{}\033[0m".format(response))
        logger.debug("<<< \033[33m{}\033[0m".format(content))
    else:
        logger.debug("<<< \033[31m{}\033[0m".format(response))
        logger.debug("<<< \033[31m{}\033[0m".format(content))


def log_debug(*msgs):
    logger.debug(" ".join(str(m) for m in msgs))
