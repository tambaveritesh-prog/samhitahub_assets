"""
Authenticated Google Drive API client factory.

Follows the design principles laid out in this module's `README.md`:

- Credentials are loaded once (from `Settings.google_service_account_json_path`)
  and cached via `functools.lru_cache`, not re-read/re-authenticated per call.
- The client factory is exposed as a FastAPI dependency provider
  (`get_google_drive_client`) so it can be swapped for a fake/mock in
  tests via `app.dependency_overrides`.
- Failures raise `GoogleDriveError`, a dedicated subclass of
  `app.core.exceptions.ExternalServiceError`.
- The `google-api-python-client` client itself is synchronous; callers
  (the repository layer) are responsible for running blocking calls via
  `asyncio.to_thread` so the event loop is never blocked.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from google.oauth2 import service_account
from googleapiclient.discovery import Resource, build

from app.core.dependencies import SettingsDep
from app.core.exceptions import ExternalServiceError

# Read-only scope is sufficient: this integration only lists/reads file
# metadata, it never downloads, modifies, or uploads content.
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class GoogleDriveError(ExternalServiceError):
    """Raised when authentication with, or a call to, Google Drive fails."""

    code = "GOOGLE_DRIVE_ERROR"


@lru_cache
def _build_client(credentials_path: str) -> Resource:
    """Build (and cache) an authenticated Drive API client for a given
    service-account credentials file path.

    Cached via `lru_cache` keyed on the credentials path so repeated
    dependency resolutions within the process reuse the same client
    instead of re-authenticating on every request.
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=DRIVE_SCOPES
        )
    except (FileNotFoundError, ValueError, OSError) as exc:
        raise GoogleDriveError(
            f"Failed to load Google service account credentials from "
            f"'{credentials_path}': {exc}"
        ) from exc

    try:
        return build("drive", "v3", credentials=credentials, cache_discovery=False)
    except Exception as exc:  # noqa: BLE001 - surfaced as a domain error
        raise GoogleDriveError(f"Failed to initialize Google Drive client: {exc}") from exc


def get_google_drive_client(settings: SettingsDep) -> Resource:
    """FastAPI dependency provider for an authenticated Drive API client.

    Reads credentials exclusively from `Settings`
    (`google_service_account_json_path`), never from the environment
    directly, per the project's configuration convention.
    """
    if not settings.google_service_account_json_path:
        raise GoogleDriveError(
            "GOOGLE_SERVICE_ACCOUNT_JSON_PATH is not configured. Set it in "
            "the environment/.env to enable the Google Drive integration."
        )
    return _build_client(settings.google_service_account_json_path)


GoogleDriveClientDep = Annotated[Resource, Depends(get_google_drive_client)]
