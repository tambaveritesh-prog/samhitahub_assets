# SamhitaHub Studio Backend

A standalone Python/FastAPI backend that will power all AI automation
for **SamhitaHub Studio** (the Android admin app). It is fully
independent of the SamhitaHub Android app and the SamhitaHub Studio
Android app — communication happens only over HTTP (and, later,
Firestore as a shared data store).

> **Status:** Architecture/scaffolding stage only. No feature logic
> (Drive, OCR, AI, Firestore, auth, etc.) is implemented yet — see
> [Roadmap](#roadmap) below. This stage establishes the structure
> everything else will be built into.

---

## Tech stack

- **Python 3.12**
- **FastAPI** — async web framework
- **Pydantic v2 / pydantic-settings** — validation & configuration
- **Uvicorn** — ASGI server
- **pytest / httpx** — testing
- **ruff / mypy** — linting & static typing
- **Docker** — containerized deployment

---

## Project structure

```
samhitahub-studio-backend/
├── app/
│   ├── main.py                  # FastAPI app factory + ASGI entrypoint
│   │
│   ├── core/                    # Cross-cutting concerns, depended on by everything
│   │   ├── config.py             # Settings (env vars), typed & validated
│   │   ├── logging.py            # Logging setup (text or JSON)
│   │   ├── exceptions.py         # Exception hierarchy + FastAPI error handlers
│   │   └── dependencies.py       # Shared DI providers (Settings, Logger)
│   │
│   ├── api/                     # HTTP transport layer (thin)
│   │   ├── deps.py                # API-layer DI providers (e.g. future auth)
│   │   └── v1/
│   │       ├── router.py          # Aggregates all v1 routers
│   │       └── endpoints/
│   │           └── health.py       # GET /api/v1/health
│   │
│   ├── models/                  # Internal domain models (storage-agnostic)
│   │   └── base.py                # BaseDomainModel (id, created_at, updated_at)
│   │
│   ├── schemas/                 # API request/response contracts (Pydantic)
│   │   ├── common.py              # Shared schema building blocks (pagination, etc.)
│   │   └── health.py              # HealthResponse
│   │
│   ├── services/                 # Business logic, orchestrates repos/modules
│   │   ├── base.py                 # BaseService (logger convenience)
│   │   └── health_service.py       # Example service + DI provider pattern
│   │
│   ├── repositories/             # Data-access abstractions
│   │   └── base.py                 # Generic async CRUD interface
│   │
│   ├── utils/                    # Pure, dependency-free helper functions
│   │   └── datetime_utils.py       # UTC time / ISO formatting helpers
│   │
│   ├── background/               # Deferred / background work
│   │   └── tasks.py                 # Placeholder background task pattern
│   │
│   └── modules/                  # Integrations with external systems
│       ├── ai/                     # AI processing (chapter/shloka detection, etc.)
│       ├── google_drive/           # Google Drive ingestion
│       └── firestore/              # Firestore publishing
│
├── tests/
│   ├── conftest.py               # Shared fixtures (test app + async client)
│   └── test_health.py            # Example endpoint test
│
├── docs/
│   └── ARCHITECTURE.md           # Deeper explanation of layering & request flow
│
├── scripts/
│   └── run_dev.sh                # Local dev convenience runner
│
├── requirements.txt              # Production dependencies (pinned)
├── requirements-dev.txt          # + testing/linting dependencies
├── pyproject.toml                # Project metadata, ruff/mypy/pytest config
├── Dockerfile                    # Multi-stage production image
├── docker-compose.yml            # Local dev orchestration
├── .env.example                  # All supported environment variables, documented
└── .gitignore
```

### Why each top-level folder exists

| Folder | Purpose |
|---|---|
| `core` | Configuration, logging, error handling, DI primitives. The foundation every other layer sits on top of. Nothing here depends on the rest of the app. |
| `api` | HTTP-only concerns: routing and request/response shaping. Kept thin on purpose — no business logic lives here. |
| `models` | How the backend represents its data internally, independent of any database or API shape. |
| `schemas` | The external contract of the API — what Android/clients actually send and receive. Allowed to diverge from `models`. |
| `services` | Where business logic and use-case orchestration lives. Framework-agnostic. |
| `repositories` | Abstracts persistence so services never talk to a database SDK directly. |
| `utils` | Small, pure, well-tested helpers with zero external dependencies. |
| `background` | Anything that runs outside the request/response cycle (today: a placeholder pattern; later: OCR/AI pipeline jobs). |
| `modules` | Self-contained wrappers around external systems (Google Drive, Firestore, AI providers). Lower-level than services. |

Full rationale for the layering and request lifecycle is in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Getting started

### Prerequisites
- Python 3.12+
- (Optional) Docker & Docker Compose

### Local setup (without Docker)

```bash
# 1. Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies (includes dev/test tooling)
pip install -r requirements-dev.txt

# 3. Configure environment
cp .env.example .env
# edit .env if needed — defaults work out of the box for local dev

# 4. Run the API
uvicorn app.main:app --reload
# or: ./scripts/run_dev.sh
```

The API will be available at `http://localhost:8000`, with interactive
docs at `http://localhost:8000/docs`.

### Local setup (with Docker)

```bash
cp .env.example .env
docker compose up --build
```

### Verifying it works

```bash
curl http://localhost:8000/api/v1/health
```

```json
{
  "status": "ok",
  "app_name": "SamhitaHub Studio Backend",
  "version": "0.1.0",
  "environment": "local"
}
```

### Running tests

```bash
pytest
```

### Linting & type-checking

```bash
ruff check .
mypy app
```

---

## Configuration

All configuration is environment-variable-driven and documented in
[`.env.example`](.env.example). See `app/core/config.py` for the
authoritative, typed definition (`Settings`).

---

## Roadmap

This repository is being built in deliberate stages. Current stage:
**architecture & scaffolding only**. Planned subsequent stages (each a
separate, focused change):

1. Google Drive integration (`app/modules/google_drive`)
2. PDF extraction
3. OCR
4. AI processing (`app/modules/ai`) — chapter detection, shloka
   detection, reference merging, structured JSON generation
5. Firestore publishing (`app/modules/firestore`)
6. User authentication
7. Background job processing (real task queue)
8. Expanded logging/observability

---

## Design principles

- **Type hints everywhere.** `mypy --strict` is configured and should
  stay green as the project grows.
- **Async where it matters.** Endpoints and services are `async def`;
  CPU-bound or blocking SDK calls (future OCR, sync Google/Firestore
  clients) should be offloaded via `asyncio.to_thread` rather than
  blocking the event loop.
- **Dependency injection over globals.** Every cross-cutting concern
  (settings, logger, services) is provided via FastAPI `Depends`, never
  imported as a module-level singleton, so it can be overridden in
  tests.
- **Errors are typed.** Business code raises `AppError` subclasses;
  HTTP status codes are decided in exactly one place
  (`app/core/exceptions.py`).
- **Documentation lives with the code.** Every module/class/function
  in this codebase has a docstring explaining *why*, not just *what*.
