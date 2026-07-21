"""
Datetime utility helpers.

Included as a first, concrete example of the `utils` convention (pure
functions, fully type-hinted, no external dependencies). Add further
helper modules (e.g. `text_utils.py`, `slug_utils.py`, `file_utils.py`)
alongside this one as they're needed by later features.
"""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC `datetime`.

    Prefer this over `datetime.utcnow()` (which returns a naive
    datetime and is deprecated) or `datetime.now()` (which is
    local-timezone-dependent and therefore non-deterministic across
    deployment environments).
    """
    return datetime.now(timezone.utc)


def to_iso8601(value: datetime) -> str:
    """Format a `datetime` as an ISO-8601 string, normalizing naive
    datetimes to UTC first so the output always has an explicit offset.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()
