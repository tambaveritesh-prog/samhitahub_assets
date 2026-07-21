"""
Shared dependency-injection providers.

FastAPI's `Depends()` mechanism is our DI container. This module centralizes
the *generic*, cross-cutting providers (settings, logger). Feature-specific
providers (e.g. "get the ChapterDetectionService") should live next to the
feature itself — typically as a `get_x_service()` function at the bottom of
the relevant `app/services/x_service.py` module — and simply compose these
base providers.

Why function-based DI instead of a global container/singleton object?
------------------------------------------------------------------------
- It's what FastAPI is built around, so it integrates natively with
  route signatures, OpenAPI generation, and testing overrides
  (`app.dependency_overrides`).
- Each provider is independently testable and mockable.
- It avoids hidden global state; dependencies are explicit in every
  function signature that needs them.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings

SettingsDep = Annotated[Settings, Depends(get_settings)]
"""Reusable type alias for injecting `Settings` into route/service
signatures, e.g.:

    @router.get("/example")
    async def example(settings: SettingsDep) -> dict:
        return {"env": settings.environment}
"""


def get_logger() -> logging.Logger:
    """Provide a module-scoped logger.

    Exists as a DI provider (rather than routes calling
    `logging.getLogger(__name__)` directly) so that request-scoped
    logging context (e.g. correlation IDs) can be injected here later
    without touching every call site.
    """
    return logging.getLogger("samhitahub")


LoggerDep = Annotated[logging.Logger, Depends(get_logger)]
