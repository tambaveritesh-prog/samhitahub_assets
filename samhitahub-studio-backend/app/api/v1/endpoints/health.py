"""
Health check endpoint.

Used by:
- Load balancers / orchestrators (Docker, Kubernetes, Cloud Run) to
  determine if the container is ready to receive traffic.
- Uptime monitoring.
- Quick manual sanity checks during development and deployment.

Deliberately has no auth requirement and does no heavy work — it should
respond in milliseconds so it's safe to poll frequently.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.health_service import HealthServiceDep

router = APIRouter()


@router.get(
    "",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns basic liveness information about the running service.",
)
async def get_health(health_service: HealthServiceDep) -> HealthResponse:
    """Return the current health status of the service."""
    return await health_service.get_status()
