import asyncio
import logging
import json

from http import HTTPStatus
from dataclasses import dataclass
from toot import __version__
from typing import Mapping, Dict, Optional, Tuple
from aiohttp import ClientSession, ClientResponse, TraceConfig

logger = logging.getLogger(__name__)

Params = Dict[str, str]
Headers = Dict[str, str]


@dataclass
class Response():
    body: str
    headers: Mapping[str, str]

    def json(self):
        return json.loads(self.body)


class ResponseError(Exception):
    """Raised when the API retruns a response with status code >= 400."""
    def __init__(self, status_code, error, description):
        self.status_code = status_code
        self.error = error
        self.description = description

        status_message = HTTPStatus(status_code).phrase
        msg = f"HTTP {status_code} {status_message}"
        msg += f". Error: {error}" if error else ""
        msg += f". Description: {description}" if description else ""
        super().__init__(msg)


async def request(method, url, **kwargs) -> Response:
    common_headers = {"User-Agent": f"toot/{__version__}"}
    trace_config = logger_trace_config()

    async with ClientSession(headers=common_headers, trace_configs=[trace_config]) as session:
        async with session.request(method, url, **kwargs) as response:
            if not response.ok:
                error, description = await get_error(response)
                raise ResponseError(response.status, error, description)

            body = await response.text()
            return Response(body, response.headers)


async def get_error(response: ClientResponse) -> Tuple[Optional[str], Optional[str]]:
    """Attempt to extract the error and error description from response body.

    See: https://docs.joinmastodon.org/entities/error/
    """
    try:
        data = await response.json()
        return data.get("error"), data.get("error_description")
    except Exception:
        pass

    return None, None


def logger_trace_config() -> TraceConfig:
    async def on_request_start(session, context, params):
        context.start = asyncio.get_event_loop().time()
        logger.debug(f">>> {params.method} {params.url}")

    async def on_request_end(session, context, params):
        elapsed = round(100 * (asyncio.get_event_loop().time() - context.start))
        logger.debug(f"<<< {params.method} {params.url} HTTP {params.response.status} {elapsed}ms")

    trace_config = TraceConfig()
    trace_config.on_request_start.append(on_request_start)
    trace_config.on_request_end.append(on_request_end)
    return trace_config
