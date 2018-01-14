from logging import getLogger

logger = getLogger('toot')


def log_request(request):
    logger.debug(">>> \033[32m{} {}\033[0m".format(request.method, request.url))

    if request.headers:
        logger.debug(">>> HEADERS: \033[33m{}\033[0m".format(request.headers))

    if request.data:
        logger.debug(">>> DATA:    \033[33m{}\033[0m".format(request.data))

    if request.files:
        logger.debug(">>> FILES:   \033[33m{}\033[0m".format(request.files))

    if request.params:
        logger.debug(">>> PARAMS:  \033[33m{}\033[0m".format(request.params))


def log_response(response):
    if response.ok:
        logger.debug("<<< \033[32m{}\033[0m".format(response))
        logger.debug("<<< \033[33m{}\033[0m".format(response.content))
    else:
        logger.debug("<<< \033[31m{}\033[0m".format(response))
        logger.debug("<<< \033[31m{}\033[0m".format(response.content))


def log_debug(*msgs):
    logger.debug(" ".join(str(m) for m in msgs))
