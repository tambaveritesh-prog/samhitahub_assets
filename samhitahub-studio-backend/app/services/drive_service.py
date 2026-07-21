"""
Google Drive service.

Business-logic layer sitting between the API endpoints and
`GoogleDriveRepository`. Responsible for:

- Validating that `Settings.google_drive_root_folder_id` is configured
  before attempting a scan.
- Translating "not found" into the standard `NotFoundError` so the
  existing `app_error_handler` produces a consistent error envelope.
- Mapping the module-internal `DriveFile` shape to the public
  `DriveFileResponse` API schema.

Follows the same pattern as `HealthService`: a plain class plus a
`get_x_service` DI provider exposed as `DriveServiceDep`.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.core.dependencies import SettingsDep
from app.core.exceptions import NotFoundError
from app.modules.google_drive.client import GoogleDriveError
from app.modules.google_drive.schemas import DriveFile
from app.repositories.drive_repository import DriveRepositoryDep, GoogleDriveRepository
from app.schemas.drive import DriveFileResponse
from app.services.base import BaseService


class DriveService(BaseService):
    """Encapsulates the logic behind the `/drive` endpoints."""

    def __init__(self, settings: SettingsDep, repository: GoogleDriveRepository) -> None:
        super().__init__()
        self._settings = settings
        self._repository = repository

    async def list_books(self) -> list[DriveFileResponse]:
        """Recursively scan the configured root folder and return every
        PDF file found beneath it.
        """
        root_folder_id = self._require_root_folder_id()
        self.logger.info("Scanning Google Drive folder '%s' for PDFs", root_folder_id)
        files = await self._repository.list_pdf_files(root_folder_id)
        return [self._to_response(file) for file in files]

    async def get_book(self, file_id: str) -> DriveFileResponse:
        """Fetch a single PDF file's metadata by its Drive file ID.

        Raises `NotFoundError` if the file doesn't exist, or exists but
        is not a PDF.
        """
        file = await self._repository.get_pdf_file(file_id)
        if file is None:
            raise NotFoundError(
                f"PDF file '{file_id}' was not found in Google Drive.",
                details={"fileId": file_id},
            )
        return self._to_response(file)

    def _require_root_folder_id(self) -> str:
        if not self._settings.google_drive_root_folder_id:
            raise GoogleDriveError(
                "GOOGLE_DRIVE_ROOT_FOLDER_ID is not configured. Set it in "
                "the environment/.env to enable the Google Drive integration."
            )
        return self._settings.google_drive_root_folder_id

    @staticmethod
    def _to_response(file: DriveFile) -> DriveFileResponse:
        return DriveFileResponse(
            file_id=file.file_id,
            name=file.name,
            modified_time=file.modified_time,
            mime_type=file.mime_type,
            size=file.size,
            parent_folder=file.parent_folder,
            drive_path=file.drive_path,
        )


def get_drive_service(settings: SettingsDep, repository: DriveRepositoryDep) -> DriveService:
    """FastAPI dependency provider for `DriveService`."""
    return DriveService(settings=settings, repository=repository)


DriveServiceDep = Annotated[DriveService, Depends(get_drive_service)]
