"""The FastAPI application."""

from __future__ import annotations

from fastapi import FastAPI

from zoo_platform import __version__
from zoo_platform.api.errors import register_error_handlers
from zoo_platform.api.middleware import AccessLogMiddleware
from zoo_platform.api.routes import (
    adoptions,
    catalog,
    health,
    internal,
    kitchen,
    owl,
    pantries,
    pens,
)
from zoo_platform.container import Container, build_container, default_adapters
from zoo_platform.infrastructure.demo import seed_demo
from zoo_platform.settings import Settings


def create_app(container: Container) -> FastAPI:
    app = FastAPI(title="Zoo Platform", version=__version__)
    app.state.container = container
    app.add_middleware(AccessLogMiddleware, clock=container.adapters.clock)
    register_error_handlers(app)
    for module in (health, owl, kitchen, catalog, adoptions, pantries, pens, internal):
        app.include_router(module.router)
    return app


def create_default_app() -> FastAPI:
    """Entry point for `uvicorn zoo_platform.api.app:create_default_app --factory`."""
    settings = Settings.from_env()
    container = build_container(settings, default_adapters(settings))
    seed_demo(container.database)
    return create_app(container)
