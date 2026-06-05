from collections.abc import Awaitable, Callable
from uuid import uuid4

import structlog
from fastapi import Request, Response
from structlog.contextvars import bind_contextvars, clear_contextvars

RequestHandler = Callable[[Request], Awaitable[Response]]


async def correlation_id_middleware(request: Request, call_next: RequestHandler) -> Response:
    clear_contextvars()
    request_id = request.headers.get("x-request-id") or str(uuid4())
    request.state.request_id = request_id
    bind_contextvars(request_id=request_id)

    logger = structlog.get_logger()
    logger.info("request.started", method=request.method, path=request.url.path)
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    logger.info("request.completed", status_code=response.status_code)
    return response

