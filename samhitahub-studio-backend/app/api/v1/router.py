"""
Aggregates all v1 endpoint routers into a single `APIRouter`.

`app.main` only needs to know about this one router (mounted under the
`api_v1_prefix` configured in `Settings`). As new endpoint modules are
added under `app/api/v1/endpoints/`, register them here — this is the
single place that defines "what exists in API v1."
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import drive, health

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(drive.router, prefix="/drive", tags=["Google Drive"])

# Future endpoint modules will be registered here, e.g.:
# from app.api.v1.endpoints import ocr, ai, chapters, shlokas, publish
# api_router.include_router(ocr.router, prefix="/ocr", tags=["OCR"])
# api_router.include_router(ai.router, prefix="/ai", tags=["AI Processing"])
