# Google Drive Module (Placeholder)

## Purpose
Encapsulates all interaction with the Google Drive API — the source of
PDFs/scanned documents that feed the AI processing pipeline.

## Planned responsibilities
- Authenticate via a Google service account
  (`Settings.google_service_account_json_path`).
- List/browse files within a configured root folder
  (`Settings.google_drive_root_folder_id`).
- Download file contents (streaming, to avoid loading large PDFs
  fully into memory where possible).
- Optionally, write processed outputs back to Drive.

## Planned structure (future stages)
```
app/modules/google_drive/
├── __init__.py
├── client.py     # Authenticated Drive API client factory
├── files.py       # List/download/upload helpers
└── schemas.py     # Drive-specific data shapes (DriveFile, etc.)
```

## Design principles to follow when implementing
- Credentials are loaded once and cached, not re-read per call.
- The client factory should be exposed as a FastAPI dependency
  provider so it can be swapped for a fake/mock in tests.
- Failures should raise a dedicated `GoogleDriveError(ExternalServiceError)`
  (subclassing `app.core.exceptions.ExternalServiceError`).
- Network calls to the Drive API should run via the official async-
  compatible approach (e.g. run the sync `google-api-python-client`
  calls in a thread pool via `asyncio.to_thread`, or use an async
  HTTP-based client) so they don't block the event loop.
