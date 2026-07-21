"""
Base domain model.

`BaseDomainModel` is the parent for all internal domain models added in
later stages (e.g. `Book`, `Chapter`, `Shloka`, `Reference`). It is a
plain Pydantic model (not tied to any database driver) so domain logic
stays storage-agnostic; repository implementations are responsible for
converting to/from whatever the underlying store (Firestore, etc.)
actually needs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class BaseDomainModel(BaseModel):
    """Common fields and configuration shared by all domain models."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
