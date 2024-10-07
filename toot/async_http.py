import logging
import time
from typing import TYPE_CHECKING, Optional, Tuple

import aiohttp
from aiohttp import ClientResponse
from aiohttp.client import _RequestOptions

from toot import App, User
from toot.cli import AsyncContext

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from typing_extensions import Unpack


class APIError(Exception):
    """Represents an error response from the API."""

    def __init__(self, message: Optional[str] = None, cause: Optional[Exception] = None):
        assert message or cause
        self.message = message or str(cause)
        self.cause = cause
        super().__init__(self.message)


class ResponseError(APIError):
    """Raised when the API returns a response with status code >= 400."""

    def __init__(self, status_code: int, error: Optional[str], description: Optional[str]):
        self.status_code = status_code
        self.error = error
        self.description = description

        msg = f"HTTP {status_code}"
        msg += f". Error: {error}" if error else ""
        msg += f". Description: {description}" if description else ""
        super().__init__(msg)


def create_client_session(user: User, app: App):
    return aiohttp.ClientSession(
        base_url=app.base_url,
        headers={"Authorization": f"Bearer {user.access_token}"},
    )


async def request(ctx: AsyncContext, method: str, url: str, **kwargs: "Unpack[_RequestOptions]") -> ClientResponse:
    started_at = time.time()
    log_request(method, url, **kwargs)

    try:
        async with ctx.session.request(method, url, **kwargs) as response:
            log_response(response, started_at)
            if response.ok:
                await response.read()
                return response
            else:
                error, description = await get_error(response)
                raise ResponseError(response.status, error, description)
    except aiohttp.ClientError as ex:
        log_error(method, url, ex)
        raise APIError(cause=ex)


def log_request(method: str, url: str, **kwargs: "Unpack[_RequestOptions]"):
    logger.info(f"--> {method} {url}")
    for key in ["params", "data", "json", "files"]:
        if key in kwargs:
            logger.debug(f"--> {key}={kwargs[key]}")


def log_response(response: ClientResponse, started_at: float):
    request = response.request_info
    duration_ms = int(1000 * (time.time() - started_at))
    logger.info(
        f"<-- {request.method} {request.url.path} HTTP {response.status} {duration_ms}ms"
    )


def log_error(method: str, url: str, ex: Exception):
    logger.error(f"<-- {method} {url} Exception: {str(ex)}")
    logger.exception(ex)


async def get_error(response: ClientResponse) -> Tuple[Optional[str], Optional[str]]:
    """Attempt to extract the error and error description from response body.

    See: https://docs.joinmastodon.org/entities/error/
    """
    try:
        data = await response.json()
        return data.get("error"), data.get("error_description")
    except Exception:
        return None, None
