# Firestore Module (Placeholder)

## Purpose
Encapsulates all interaction with Google Cloud Firestore — the
destination datastore that the SamhitaHub Android app reads from.

## Planned responsibilities
- Authenticate using `Settings.firestore_project_id` /
  `Settings.firestore_credentials_path`.
- Provide an async-friendly client for reading/writing documents.
- Serve as the concrete implementation target for repositories defined
  under `app/repositories/` (e.g. a future `FirestoreBookRepository`
  implementing `app.repositories.base.BaseRepository`).

## Planned structure (future stages)
```
app/modules/firestore/
├── __init__.py
├── client.py           # Authenticated Firestore client factory
└── converters.py        # Domain model <-> Firestore document mapping
```

## Design principles to follow when implementing
- The `google-cloud-firestore` Python client is sync; wrap calls with
  `asyncio.to_thread` (or use the library's async client where
  available) so Firestore I/O never blocks the event loop.
- Keep Firestore-specific document shapes (field names, nested map
  structures) confined to `converters.py` — the rest of the app should
  only ever see `app.models` domain objects, never raw Firestore
  dicts.
- Failures should raise a dedicated `FirestoreError(ExternalServiceError)`
  (subclassing `app.core.exceptions.ExternalServiceError`).
