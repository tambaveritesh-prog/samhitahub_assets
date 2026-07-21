"""Schemas for the health check endpoint."""

from __future__ import annotations

from app.schemas.common import APIModel


class HealthResponse(APIModel):
    """Response body for `GET /api/v1/health`."""

    status: str
    app_name: str
    version: str
    environment: str
