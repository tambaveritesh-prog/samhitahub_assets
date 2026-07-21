"""
Base repository abstraction.

`BaseRepository` is a generic abstract interface for simple CRUD-style
data access, parameterized by the domain model type it manages. Concrete
entity repositories (e.g. a future `BookRepository`) should subclass
this and implement each method against the actual data store (Firestore,
initially).

Using `abc.ABC` + `typing.Generic` here (rather than `typing.Protocol`)
is a deliberate choice: we want subclasses to be forced to implement
every method (enforced at instantiation time), which catches
incomplete implementations early during development.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

from app.models.base import BaseDomainModel

ModelT = TypeVar("ModelT", bound=BaseDomainModel)


class BaseRepository(ABC, Generic[ModelT]):
    """Generic async CRUD interface implemented by concrete repositories."""

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> ModelT | None:
        """Fetch a single entity by its ID, or `None` if not found."""
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> list[ModelT]:
        """Fetch all entities. Replace/extend with filtering & pagination
        parameters once real query patterns are known.
        """
        raise NotImplementedError

    @abstractmethod
    async def create(self, entity: ModelT) -> ModelT:
        """Persist a new entity and return the stored representation."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, entity: ModelT) -> ModelT:
        """Persist changes to an existing entity."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, entity_id: UUID) -> None:
        """Delete an entity by its ID. Should be a no-op if it doesn't exist."""
        raise NotImplementedError
