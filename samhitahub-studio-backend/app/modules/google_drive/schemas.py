"""
Google Drive module-internal data shapes.

`DriveFile` is the internal representation of a PDF file discovered in
Google Drive, produced by `GoogleDriveRepository` and consumed by
`DriveService`. It is intentionally decoupled from the public API
schema (`app.schemas.drive.DriveFileResponse`) so that the module's
internal shape can evolve independently of the wire contract, and so
this module has no dependency on the API layer (matching the
dependency direction used elsewhere in the codebase: modules/repositories
are lower-level than services, which are lower-level than the API).
"""

from __future__ import annotations

from pydantic import BaseModel


class DriveFile(BaseModel):
    """A single PDF file discovered while scanning Google Drive."""

    file_id: str
    name: str
    modified_time: str
    mime_type: str
    size: int | None
    parent_folder: str
    drive_path: str
