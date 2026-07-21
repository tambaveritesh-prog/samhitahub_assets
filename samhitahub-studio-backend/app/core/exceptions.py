"""
Application-wide exception hierarchy and FastAPI exception handlers.

Why a custom hierarchy?
------------------------
Letting every layer raise ad-hoc `HTTPException`s couples business logic
(services/repositories) to the web framework and leads to inconsistent
error payloads. Instead:

1. Domain/service/repository code raises subclasses of `AppError`.
2. A single set of FastAPI exception handlers (registered in
   `app.main`) translates `AppError` subclasses into a consistent JSON
   error envelope with the right HTTP status code.
3. Any *unexpected* exception is caught by a catch-all handler, logged
   with a stack trace, and turned into a generic 500 response — so
   internal details never leak to API clients.

Error response shape
---------------------
    {
        "error": {
            "code": "NOT_FOUND",
            "message": "Document 'abc123' was not found.",
            "details": null
        }
    }

This shape is stable and versioned independently of the exception
class names, so clients can reliably branch on `error.code`.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base class for all application-raised (expected) errors.

    Attributes:
        message: Human-readable message safe to return to API clients.
        code: Short, machine-readable error code (stable API contract).
        status_code: HTTP status code to respond with.
        details: Optional structured extra context (validation errors,
            offending field names, etc.).
    """

    code: str = "APP_ERROR"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    code = "NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class ValidationError(AppError):
    """Raised for domain-level validation failures (not FastAPI/pydantic
    request-parsing errors, which are handled separately and automatically
    by FastAPI itself).
    """

    code = "VALIDATION_ERROR"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class ConflictError(AppError):
    """Raised when an operation conflicts with the current state of a
    resource (e.g. duplicate creation, optimistic-locking mismatch).
    """

    code = "CONFLICT"
    status_code = status.HTTP_409_CONFLICT


class UnauthorizedError(AppError):
    """Raised when a request lacks valid authentication credentials."""

    code = "UNAUTHORIZED"
    status_code = status.HTTP_401_UNAUTHORIZED


class ForbiddenError(AppError):
    """Raised when an authenticated caller lacks permission for an action."""

    code = "FORBIDDEN"
    status_code = status.HTTP_403_FORBIDDEN


class ExternalServiceError(AppError):
    """Raised when a downstream dependency (Google Drive, Firestore, an AI
    provider, etc.) fails or returns an unexpected response.

    Kept generic here; feature modules are expected to subclass this
    (e.g. `GoogleDriveError(ExternalServiceError)`) once implemented.
    """

    code = "EXTERNAL_SERVICE_ERROR"
    status_code = status.HTTP_502_BAD_GATEWAY


class ErrorDetail(BaseModel):
    """Schema for the nested `error` object in an error response."""

    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Top-level schema for all error responses returned by the API."""

    error: ErrorDetail


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Translate an `AppError` into the standard JSON error envelope."""
    logger.warning(
        "Handled application error",
        extra={
            "path": request.url.path,
            "error_code": exc.code,
            "status_code": exc.status_code,
        },
    )
    payload = ErrorResponse(
        error=ErrorDetail(code=exc.code, message=exc.message, details=exc.details)
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected exceptions.

    Logs the full stack trace server-side but returns a deliberately
    generic message to the client to avoid leaking internals.
    """
    logger.exception(
        "Unhandled exception while processing request",
        extra={"path": request.url.path},
    )
    payload = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred. Please try again later.",
        )
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=payload.model_dump(),
    )
