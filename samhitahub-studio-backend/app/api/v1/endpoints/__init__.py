"""
Endpoint modules for API v1.

Convention: one file per resource/feature area (e.g. `health.py`,
later `drive.py`, `ocr.py`, `ai.py`, `chapters.py`, `shlokas.py`,
`publish.py`, `auth.py`). Each file defines its own `APIRouter` named
`router`, which gets included by `app.api.v1.router`.
"""
