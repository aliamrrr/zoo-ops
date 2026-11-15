"""Maps domain errors to HTTP responses."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from zoo_platform.domain.errors import (
    Conflict,
    Forbidden,
    InvalidRequest,
    NotFound,
    ProviderRejected,
    ProviderUnavailable,
    Unauthorized,
    ZooError,
)

STATUS_BY_ERROR: list[tuple[type[ZooError], int]] = [
    (NotFound, 404),
    (Conflict, 409),
    (InvalidRequest, 422),
    (Unauthorized, 401),
    (Forbidden, 403),
    (ProviderRejected, 422),
    (ProviderUnavailable, 502),
]


def status_for(error: ZooError) -> int:
    return next((status for kind, status in STATUS_BY_ERROR if isinstance(error, kind)), 500)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ZooError)
    async def handle_zoo_error(request: Request, error: ZooError) -> JSONResponse:
        return JSONResponse(
            {"error": error.code, "detail": str(error)}, status_code=status_for(error)
        )
