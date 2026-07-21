"""
Health service.

Deliberately simple, but included from day one to establish the
pattern every future service should follow: a class in `app/services/`
plus a `get_x_service` DI provider that endpoint modules depend on,
rather than importing/instantiating the service directly. This keeps
services swappable in tests via `app.dependency_overrides`.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.core.dependencies import SettingsDep
from app.schemas.health import HealthResponse
from app.services.base import BaseService


class HealthService(BaseService):
    """Encapsulates the logic behind the `/health` endpoint.

    Currently reports static/config-derived info. Future extensions
    (checking Firestore connectivity, Google Drive auth validity, AI
    provider reachability, background worker liveness, etc.) should be
    added as additional checks here, aggregated into the response.
    """

    def __init__(self, settings: SettingsDep) -> None:
        super().__init__()
        self._settings = settings

    async def get_status(self) -> HealthResponse:
        """Return the current health status of the service."""
        return HealthResponse(
            status="ok",
            app_name=self._settings.app_name,
            version=self._settings.app_version,
            environment=self._settings.environment.value,
        )


def get_health_service(settings: SettingsDep) -> HealthService:
    """FastAPI dependency provider for `HealthService`."""
    return HealthService(settings=settings)


HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]
