"""
Application entrypoint.

Defines `create_app()`, an application-factory function that builds and
configures the FastAPI instance. Using a factory (rather than a bare
module-level `app = FastAPI()`) is a deliberate best practice:

- Tests can call `create_app()` with overridden settings to get a
  fresh, isolated app instance per test/test-session.
- It makes the startup sequence (logging -> settings -> app ->
  middleware -> routers -> exception handlers) explicit and ordered in
  one place instead of scattered module-level side effects.

Run locally with:
    uvicorn app.main:app --reload

The module-level `app` object at the bottom exists because ASGI
servers (uvicorn/gunicorn) need an importable `module:attribute`
target — it's simply `create_app()` called once at import time.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.exceptions import (
    AppError,
    app_error_handler,
    unhandled_exception_handler,
)
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage startup/shutdown events.

    This is the designated place to initialize and tear down
    long-lived resources later (e.g. an HTTP client pool for the AI
    provider, a Firestore client, a background task-queue connection).
    Nothing to initialize yet at this stage.
    """
    settings: Settings = app.state.settings
    logger = logging.getLogger("samhitahub")
    logger.info(
        "Starting %s v%s in %s mode",
        settings.app_name,
        settings.app_version,
        settings.environment.value,
    )
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure a `FastAPI` application instance.

    Args:
        settings: Optional explicit `Settings` instance, primarily for
            tests. Defaults to the cached process-wide settings via
            `get_settings()`.
    """
    resolved_settings = settings or get_settings()

    configure_logging(resolved_settings)

    app = FastAPI(
        title=resolved_settings.app_name,
        version=__version__,
        description=(
            "AI automation backend for SamhitaHub Studio. Handles Google "
            "Drive ingestion, OCR, AI-assisted chapter/shloka detection, "
            "reference merging, JSON generation, and Firestore publishing."
        ),
        docs_url="/docs" if resolved_settings.docs_enabled else None,
        redoc_url="/redoc" if resolved_settings.docs_enabled else None,
        openapi_url="/openapi.json" if resolved_settings.docs_enabled else None,
        lifespan=lifespan,
    )

    # Stash settings on app.state so the lifespan handler (and anything
    # else with access to the `app`/`request` object) can reach it
    # without re-reading the environment.
    app.state.settings = resolved_settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(api_router, prefix=resolved_settings.api_v1_prefix)

    return app


app = create_app()
