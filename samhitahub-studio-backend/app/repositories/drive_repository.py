"""
Google Drive repository.

Encapsulates all direct calls to the Google Drive API (`files().list()` /
`files().get()`). Deliberately does **not** subclass
`app.repositories.base.BaseRepository`: that abstraction models CRUD
access to entities we own and persist (keyed by `UUID`, with
create/update/delete), whereas this repository is a **read-only** view
over an external system (Drive), keyed by Drive's own string file IDs.
Forcing it into the CRUD interface would mean faking `create`/`update`/
`delete` methods that can never legitimately be implemented, which is
worse than simply not inheriting it. The layering convention (API ->
service -> repository -> data source) is otherwise followed exactly.

Only PDF files (`mimeType == "application/pdf"`) are ever returned, per
the feature requirements. No file content is downloaded — only
metadata.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Annotated

from fastapi import Depends
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from app.modules.google_drive.client import GoogleDriveClientDep, GoogleDriveError
from app.modules.google_drive.schemas import DriveFile

logger = logging.getLogger(__name__)

_PDF_MIME_TYPE = "application/pdf"
_FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"

_FILE_LIST_FIELDS = "nextPageToken, files(id, name, mimeType, modifiedTime, size)"
_FILE_GET_FIELDS = "id, name, mimeType, modifiedTime, size, parents"


class GoogleDriveRepository:
    """Data-access layer for reading PDF file metadata from Google Drive."""

    def __init__(self, client: Resource) -> None:
        self._client = client

    # -- Public API -------------------------------------------------------

    async def list_pdf_files(self, root_folder_id: str) -> list[DriveFile]:
        """Recursively scan `root_folder_id` and every subfolder beneath
        it, returning metadata for every PDF file found.
        """
        return await asyncio.to_thread(self._list_pdf_files_sync, root_folder_id)

    async def get_pdf_file(self, file_id: str) -> DriveFile | None:
        """Fetch a single PDF file's metadata by its Drive file ID.

        Returns `None` if no such file exists, or if it exists but is
        not a PDF (mirroring the fact that `list_pdf_files` would never
        have surfaced it either).
        """
        return await asyncio.to_thread(self._get_pdf_file_sync, file_id)

    # -- Sync implementation (run off the event loop via to_thread) -------

    def _list_pdf_files_sync(self, root_folder_id: str) -> list[DriveFile]:
        root_name = self._get_folder_name(root_folder_id)
        files: list[DriveFile] = []
        self._scan_folder(folder_id=root_folder_id, folder_path=root_name, files=files)
        return files

    def _scan_folder(self, *, folder_id: str, folder_path: str, files: list[DriveFile]) -> None:
        """Depth-first recursive scan of `folder_id`, appending any PDF
        files found (in this folder and all descendants) to `files`.
        """
        for item in self._list_children(folder_id, mime_type=_PDF_MIME_TYPE):
            files.append(
                DriveFile(
                    file_id=item["id"],
                    name=item["name"],
                    modified_time=item["modifiedTime"],
                    mime_type=item["mimeType"],
                    size=self._parse_size(item.get("size")),
                    parent_folder=folder_id,
                    drive_path=f"{folder_path}/{item['name']}",
                )
            )

        for subfolder in self._list_children(folder_id, mime_type=_FOLDER_MIME_TYPE):
            self._scan_folder(
                folder_id=subfolder["id"],
                folder_path=f"{folder_path}/{subfolder['name']}",
                files=files,
            )

    def _get_pdf_file_sync(self, file_id: str) -> DriveFile | None:
        try:
            item = self._client.files().get(fileId=file_id, fields=_FILE_GET_FIELDS).execute()
        except HttpError as exc:
            if getattr(exc.resp, "status", None) == 404:
                return None
            raise GoogleDriveError(
                f"Google Drive API error while fetching file '{file_id}': {exc}"
            ) from exc

        if item.get("mimeType") != _PDF_MIME_TYPE:
            return None

        parents = item.get("parents") or []
        parent_folder = parents[0] if parents else ""
        drive_path = self._build_drive_path(parent_folder, item["name"])

        return DriveFile(
            file_id=item["id"],
            name=item["name"],
            modified_time=item["modifiedTime"],
            mime_type=item["mimeType"],
            size=self._parse_size(item.get("size")),
            parent_folder=parent_folder,
            drive_path=drive_path,
        )

    # -- Low-level helpers --------------------------------------------------

    def _list_children(self, folder_id: str, *, mime_type: str) -> list[dict]:
        """List all direct children of `folder_id` matching `mime_type`,
        transparently paging through all result pages.
        """
        query = f"'{folder_id}' in parents and trashed = false and mimeType = '{mime_type}'"
        items: list[dict] = []
        page_token: str | None = None

        while True:
            try:
                response = (
                    self._client.files()
                    .list(
                        q=query,
                        spaces="drive",
                        fields=_FILE_LIST_FIELDS,
                        pageToken=page_token,
                        pageSize=1000,
                    )
                    .execute()
                )
            except HttpError as exc:
                raise GoogleDriveError(
                    f"Google Drive API error while listing children of folder "
                    f"'{folder_id}': {exc}"
                ) from exc

            items.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return items

    def _get_folder_name(self, folder_id: str) -> str:
        try:
            folder = self._client.files().get(fileId=folder_id, fields="id, name").execute()
        except HttpError as exc:
            raise GoogleDriveError(
                f"Google Drive API error while resolving root folder "
                f"'{folder_id}': {exc}"
            ) from exc
        return folder.get("name", folder_id)

    def _build_drive_path(self, parent_folder_id: str, file_name: str) -> str:
        """Walk up the parent chain from `parent_folder_id` to build a
        human-readable `/`-separated path ending in `file_name`.
        """
        segments = [file_name]
        current_id: str | None = parent_folder_id

        # Defensive cap: Drive folder structures are trees in practice,
        # but guard against unexpectedly deep/cyclic parent chains.
        for _ in range(64):
            if not current_id:
                break
            try:
                folder = (
                    self._client.files()
                    .get(fileId=current_id, fields="id, name, parents")
                    .execute()
                )
            except HttpError:
                logger.warning(
                    "Could not resolve Drive folder '%s' while building path; "
                    "truncating path here.",
                    current_id,
                )
                break

            segments.append(folder.get("name", current_id))
            parents = folder.get("parents") or []
            current_id = parents[0] if parents else None

        segments.reverse()
        return "/".join(segments)

    @staticmethod
    def _parse_size(raw_size: str | None) -> int | None:
        """Drive returns `size` as a string (it can exceed 32 bits); we
        expose it as an `int` for convenience, treating missing/invalid
        values (e.g. Google-native docs have no `size`) as `None`.
        """
        if raw_size is None:
            return None
        try:
            return int(raw_size)
        except ValueError:
            return None


def get_drive_repository(client: GoogleDriveClientDep) -> GoogleDriveRepository:
    """FastAPI dependency provider for `GoogleDriveRepository`."""
    return GoogleDriveRepository(client=client)


DriveRepositoryDep = Annotated[GoogleDriveRepository, Depends(get_drive_repository)]
