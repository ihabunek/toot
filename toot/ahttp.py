import asyncio
import logging
import json

from aiohttp import ClientResponse, TraceConfig
from dataclasses import dataclass
from functools import lru_cache
from http import HTTPStatus
from toot import Context
from typing import Any, Mapping, Dict, Optional, Tuple


logger = logging.getLogger(__name__)

Params = Dict[str, str]
Headers = Dict[str, str]
Json = Dict[str, Any]


@dataclass(frozen=True)
class Response():
    body: str
    headers: Mapping[str, str]

    @property
    # @lru_cache
    def json(self) -> Json:
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


async def request(ctx: Context, method: str, url: str, **kwargs) -> Response:
    async with ctx.session.request(method, url, **kwargs) as response:
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
        logger.debug(f"--> {params.method} {params.url}")

    async def on_request_end(session, context, params):
        elapsed = round(100 * (asyncio.get_event_loop().time() - context.start))
        logger.debug(f"<-- {params.method} {params.url} HTTP {params.response.status} {elapsed}ms")

    trace_config = TraceConfig()
    trace_config.on_request_start.append(on_request_start)
    trace_config.on_request_end.append(on_request_end)
    return trace_config
