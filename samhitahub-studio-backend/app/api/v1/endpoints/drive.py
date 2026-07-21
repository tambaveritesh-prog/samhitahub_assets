"""
Google Drive endpoints.

Read-only endpoints for browsing PDF files ("books") available in the
configured Google Drive folder. No downloading, OCR, or AI processing
happens here — this module only surfaces file metadata.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.drive import DriveFileResponse
from app.services.drive_service import DriveServiceDep

router = APIRouter()


@router.get(
    "/books",
    response_model=list[DriveFileResponse],
    summary="List PDF books in Google Drive",
    description=(
        "Recursively scans the configured Google Drive root folder and all "
        "of its subfolders, returning metadata for every PDF file found."
    ),
)
async def list_books(drive_service: DriveServiceDep) -> list[DriveFileResponse]:
    """Return metadata for every PDF file under the configured root folder."""
    return await drive_service.list_books()


@router.get(
    "/book/{file_id}",
    response_model=DriveFileResponse,
    summary="Get a single PDF book by Drive file ID",
    description="Fetches metadata for a single PDF file in Google Drive by its file ID.",
)
async def get_book(file_id: str, drive_service: DriveServiceDep) -> DriveFileResponse:
    """Return metadata for a single PDF file, given its Drive file ID."""
    return await drive_service.get_book(file_id)
