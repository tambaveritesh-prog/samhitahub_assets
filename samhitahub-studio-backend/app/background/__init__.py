"""
Background package.

Home for anything that runs outside the request/response cycle:
long-running or deferred work such as PDF processing pipelines, OCR
batches, AI processing jobs, and Firestore publishing jobs.

Two tiers are anticipated as the project grows:

1. Lightweight, in-process tasks using FastAPI's built-in
   `BackgroundTasks` — fine for quick fire-and-forget work tied to a
   single request's lifecycle. See `tasks.py` for the placeholder
   pattern.
2. A real task queue (e.g. Celery, arq, or Dramatiq backed by Redis)
   for durable, retryable, potentially long-running jobs that must
   survive a process restart — appropriate once OCR/AI pipelines are
   implemented. When that's introduced, it should live under
   `app/background/worker.py` (the queue app/entrypoint) plus one
   module per job type (e.g. `app/background/jobs/ocr_job.py`).

Nothing here is wired up yet — this stage only establishes the folder
and the intended pattern.
"""
