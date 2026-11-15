"""HTTP middleware."""

from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from zoo_platform.ports import Clock

logger = logging.getLogger("zoo.access")


class AccessLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, clock: Clock) -> None:
        super().__init__(app)
        self._clock = clock

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        started = self._clock()
        response = await call_next(request)
        elapsed_ms = (self._clock() - started) * 1000
        logger.info(
            "%s %s %s %.1fms", request.method, request.url.path, response.status_code, elapsed_ms
        )
        return response
