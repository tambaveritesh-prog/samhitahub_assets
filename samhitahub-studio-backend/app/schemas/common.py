"""
Common, reusable API schemas shared across multiple endpoint modules.

Add generic building blocks here (pagination envelopes, generic
success wrappers, etc.) as they're needed. Feature-specific schemas
belong in their own file (e.g. `app/schemas/chapter.py`,
`app/schemas/shloka.py`) once those features are implemented — this
file is only for things genuinely shared across features.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class APIModel(BaseModel):
    """Base class for all API schemas.

    Centralizing `model_config` here means every schema in the project
    gets consistent behavior (e.g. populate-by-field-name) without
    repeating the config block everywhere.
    """

    model_config = ConfigDict(populate_by_name=True)


class PaginationParams(APIModel):
    """Standard pagination query parameters for list endpoints."""

    page: int = Field(default=1, ge=1, description="1-indexed page number.")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Number of items per page."
    )


class PaginatedResponse(APIModel, Generic[T]):
    """Standard envelope for paginated list responses."""

    items: list[T]
    page: int
    page_size: int
    total_items: int
    total_pages: int
