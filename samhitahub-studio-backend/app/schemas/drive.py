"""Schemas for the Google Drive endpoints (`/api/v1/drive/...`)."""

from __future__ import annotations

from pydantic import Field

from app.schemas.common import APIModel


class DriveFileResponse(APIModel):
    """Response body describing a single PDF file found in Google Drive.

    Field names are exposed in the wire format via aliases (`fileId`,
    `modifiedTime`, `mimeType`, `parentFolder`, `drivePath`) while the
    Python attribute names stay `snake_case`, consistent with
    `APIModel`'s `populate_by_name=True` configuration.
    """

    file_id: str = Field(alias="fileId", description="Google Drive file ID.")
    name: str = Field(description="File name, including extension.")
    modified_time: str = Field(
        alias="modifiedTime",
        description="RFC 3339 timestamp of the file's last modification, as reported by Drive.",
    )
    mime_type: str = Field(alias="mimeType", description="Always 'application/pdf'.")
    size: int | None = Field(
        default=None, description="File size in bytes, if reported by Drive."
    )
    parent_folder: str = Field(
        alias="parentFolder", description="Drive folder ID of the file's immediate parent."
    )
    drive_path: str = Field(
        alias="drivePath",
        description="Human-readable '/'-separated path from the configured root folder to the file.",
    )
