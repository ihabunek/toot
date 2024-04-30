import asyncio
import logging

from types import SimpleNamespace
from typing import Optional, Tuple
from aiohttp import (
    ClientResponse,
    ClientSession,
    TraceConfig,
    TraceRequestEndParams,
    TraceRequestStartParams,
)
from toot import __version__
from toot.cli import Context


logger = logging.getLogger(__name__)


async def make_session(context: Context) -> ClientSession:
    base_url = context.app.base_url if context.app else None
    headers = {"User-Agent": f"toot/{__version__}"}

    if context.user:
        headers["Authorization"] = f"Bearer {context.user.access_token}"

    trace_config = logger_trace_config()

    return ClientSession(
        headers=headers,
        base_url=base_url,
        trace_configs=[trace_config],
    )


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
    async def on_request_start(
        session: ClientSession,
        context: SimpleNamespace,
        params: TraceRequestStartParams,
    ):
        context.start = asyncio.get_event_loop().time()
        logger.debug(f"--> {params.method} {params.url}")

    async def on_request_end(
        session: ClientSession,
        context: SimpleNamespace,
        params: TraceRequestEndParams,
    ):
        elapsed = round(1000 * (asyncio.get_event_loop().time() - context.start))
        logger.debug(
            f"<-- {params.method} {params.url} HTTP {params.response.status} {elapsed}ms"
        )

    trace_config = TraceConfig()
    trace_config.on_request_start.append(on_request_start)
    trace_config.on_request_end.append(on_request_end)
    return trace_config


async def verify_credentials(session: ClientSession) -> ClientResponse:
    return await session.get("/api/v1/accounts/verify_credentials")


async def fetch_status(session: ClientSession, status_id: str) -> ClientResponse:
    """
    Fetch a single status
    https://docs.joinmastodon.org/methods/statuses/#get
    """
    return await session.get(f"/api/v1/statuses/{status_id}")
