"""
Background task placeholders.

Demonstrates the intended shape of a background task before any real
jobs (OCR, AI processing, Firestore publishing) are implemented. Real
tasks should:

- Accept plain, serializable arguments (IDs, not live objects) so they
  can later be moved to a real task queue with minimal change.
- Do their own error handling/logging internally, since exceptions
  raised inside a `BackgroundTasks` callback are NOT surfaced to the
  original HTTP response.
- Be registered from an endpoint via
  `background_tasks.add_task(my_task, ...)`.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def example_placeholder_task(identifier: str) -> None:
    """Example no-op background task.

    Replace with real tasks such as `process_uploaded_pdf`,
    `run_ocr_batch`, or `publish_to_firestore` once those modules
    exist. Kept here only to establish the pattern and confirm the
    background-task wiring works end-to-end.
    """
    logger.info("Background task executed", extra={"identifier": identifier})
