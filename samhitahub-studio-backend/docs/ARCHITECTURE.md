# Architecture

## Layering

The backend follows a layered architecture, with a strict inward
dependency direction:

```
api  ->  services  ->  repositories  ->  modules (google_drive, firestore, ai)
  \-> schemas                 \-> models
core is depended on by everything; core depends on nothing else in the app.
```

- **`api`** — HTTP transport only. Parses requests, calls services,
  returns responses. No business logic.
- **`services`** — business/application logic and orchestration. Framework-
  agnostic (no FastAPI imports, no HTTP status codes). Raises
  `app.core.exceptions.AppError` subclasses on failure.
- **`repositories`** — data access abstractions. Services depend on
  repository *interfaces*; concrete implementations (e.g. Firestore-backed)
  are swappable.
- **`modules`** — integrations with external systems/capabilities
  (Google Drive, Firestore, AI providers, and later OCR). Lower-level
  than services; a service composes one or more modules.
- **`models`** — internal domain representation.
- **`schemas`** — external API contract (request/response bodies).
- **`core`** — configuration, logging, exceptions, DI primitives. The
  foundation every other layer sits on.

This separation means, for example, that swapping the AI provider or
moving from Firestore to another database touches only the relevant
`modules`/`repositories` code — services and the API contract stay
stable.

## Request lifecycle

1. `uvicorn` receives an HTTP request and hands it to the FastAPI `app`
   built by `app.main.create_app()`.
2. FastAPI routes it to the matching endpoint function in
   `app/api/v1/endpoints/*.py` based on the router registered in
   `app/api/v1/router.py`.
3. FastAPI resolves the endpoint's dependencies (via `Depends(...)`,
   e.g. `HealthServiceDep`), instantiating services with their own
   dependencies (e.g. `Settings`) already injected.
4. The endpoint calls into the service, which contains the actual
   logic and (in later stages) orchestrates repositories/modules.
5. The service returns a Pydantic schema (or raises an `AppError`).
6. FastAPI serializes the schema to JSON. If an `AppError` was raised,
   the handlers registered in `app.main` (from
   `app.core.exceptions`) convert it to the standard error envelope.

## Configuration

All configuration flows through `app.core.config.Settings`, populated
from environment variables (see `.env.example`). Nothing else in the
codebase reads `os.environ` directly. `get_settings()` is cached
per-process and injected via FastAPI `Depends`, which also makes it
trivial to override in tests.

## Error handling

Business/domain code raises typed exceptions from
`app.core.exceptions` (`NotFoundError`, `ValidationError`,
`ConflictError`, `UnauthorizedError`, `ForbiddenError`,
`ExternalServiceError`, or a future subclass of one of these).
Two handlers registered on the `FastAPI` app in `app.main` translate
these — and any unexpected exception — into a single, stable JSON
error shape:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "...",
    "details": null
  }
}
```

## API versioning

Endpoints live under `app/api/v1/`. A future breaking change ships as
`app/api/v2/`, mounted alongside `v1` (both can run simultaneously
during a client migration window), rather than mutating `v1` in place.

## Background work

`app/background/` currently holds only a placeholder pattern using
FastAPI's built-in `BackgroundTasks`. Once OCR/AI pipelines need
durable, retryable execution (surviving process restarts, retries with
backoff, etc.), introduce a real task queue (Celery/arq/Dramatiq) here
— see the docstring in `app/background/__init__.py` for the intended
structure.

## Why this structure scales

- **New features are additive.** Adding "chapter detection" means
  adding `app/api/v1/endpoints/chapters.py`,
  `app/services/chapter_service.py`,
  `app/repositories/chapter_repository.py` (if persisted), and
  `app/schemas/chapter.py` — without modifying unrelated files.
- **Testability.** Every layer is injected via `Depends`, so any layer
  can be swapped for a fake/mock in tests (see `tests/conftest.py`).
- **Enterprise-friendly.** Clear ownership boundaries per folder make
  it straightforward to divide work across a team without merge
  conflicts in shared files.
