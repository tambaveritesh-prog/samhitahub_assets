"""
Logging configuration.

Provides a single `configure_logging()` entry point that sets up the root
logger for the entire process. Call this exactly once, as early as
possible (currently done in `app.main` before the FastAPI app is built).

Two output modes are supported, controlled by `Settings.log_json`:

- Human-readable text (good for local development).
- Structured JSON, one object per line (good for production log
  aggregators like CloudWatch, Stackdriver, ELK, etc. — easy to parse,
  filter, and index).

Design notes
------------
We intentionally avoid third-party logging frameworks here. The stdlib
`logging` module is sufficient for this stage and keeps the dependency
footprint small; a structured-logging library (e.g. `structlog`) can be
swapped in later behind this same `configure_logging()` interface
without touching call sites, since the rest of the codebase only ever
does `logging.getLogger(__name__)`.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from app.core.config import Settings


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects.

    Each record includes a fixed set of fields plus any `extra=` kwargs
    passed to the logging call, which makes it easy to attach
    request-scoped context (e.g. `request_id`) later without changing
    this formatter.
    """

    # Attributes present on every stdlib LogRecord that we don't want to
    # re-emit as "extra" fields (they're already represented explicitly).
    _RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys())

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in self._RESERVED
        }
        if extras:
            payload["extra"] = extras

        return json.dumps(payload, default=str)


def configure_logging(settings: Settings) -> None:
    """Configure the root logger according to `settings`.

    Idempotent: safe to call multiple times (e.g. across test setup) —
    existing handlers on the root logger are cleared first so log lines
    are never duplicated.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.value)

    for existing_handler in list(root_logger.handlers):
        root_logger.removeHandler(existing_handler)

    handler = logging.StreamHandler(stream=sys.stdout)

    if settings.log_json:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger.addHandler(handler)

    # Quiet down noisy third-party loggers unless we're in DEBUG.
    if settings.log_level.value != "DEBUG":
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
