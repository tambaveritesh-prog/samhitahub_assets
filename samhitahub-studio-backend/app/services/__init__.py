"""
Services package.

Contains business/application logic. Services orchestrate one or more
repositories and/or modules (Google Drive, OCR, AI, Firestore, ...) to
fulfil a use case, and are what `api` endpoint handlers call into.

Rules of thumb for this layer:
- Services know nothing about HTTP (no `Request`/`Response`, no status
  codes) — they raise `app.core.exceptions.AppError` subclasses on
  failure, which the API layer's exception handlers translate to HTTP.
- Services know nothing about *how* data is persisted — they depend on
  repository interfaces, not concrete database clients.
- Each service is exposed via a small `get_x_service()` FastAPI
  dependency provider at the bottom of its module, following the same
  pattern as `app/core/dependencies.py`.
"""
