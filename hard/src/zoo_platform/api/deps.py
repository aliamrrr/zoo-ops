"""FastAPI dependencies shared by the routers."""

from __future__ import annotations

from fastapi import Depends, Request

from zoo_platform.api.security import authenticate
from zoo_platform.container import Container
from zoo_platform.domain.models import Principal


def get_container(request: Request) -> Container:
    return request.app.state.container  # type: ignore[no-any-return]


def current_principal(request: Request, container: Container = Depends(get_container)) -> Principal:
    return authenticate(request.headers, container.settings)
