"""
Google Drive module.

Houses the authenticated Drive API client factory (`client.py`) and the
module-internal `DriveFile` data shape (`schemas.py`) used for reading
PDF file metadata from Google Drive via a service account. See
`README.md` in this directory for the full design.

The repository (`app.repositories.drive_repository`) and service
(`app.services.drive_service`) that build on top of this module live in
their usual top-level locations, per the project's layering convention.
"""

