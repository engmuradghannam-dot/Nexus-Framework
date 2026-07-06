"""
Base Service Layer for Nexus Framework
Implements Clean Architecture principles:
- Domain logic separated from infrastructure
- Services are framework-agnostic
- Repositories abstract data access
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any
from django.db import transaction

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Abstract repository for data access."""

    @abstractmethod
    def get(self, id: int) -> Optional[T]:
        pass

    @abstractmethod
    def list(self, filters: Dict = None) -> List[T]:
        pass

    @abstractmethod
    def create(self, data: Dict) -> T:
        pass

    @abstractmethod
    def update(self, id: int, data: Dict) -> T:
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        pass


class BaseService(ABC, Generic[T]):
    """
    Base service class implementing business logic.
    Services are framework-agnostic and testable.
    """

    def __init__(self, repository: BaseRepository[T]):
        self.repository = repository

    def get(self, id: int) -> Optional[T]:
        return self.repository.get(id)

    def list(self, filters: Dict = None) -> List[T]:
        return self.repository.list(filters)

    @transaction.atomic
    def create(self, data: Dict) -> T:
        self.validate_create(data)
        return self.repository.create(data)

    @transaction.atomic
    def update(self, id: int, data: Dict) -> T:
        self.validate_update(id, data)
        return self.repository.update(id, data)

    @transaction.atomic
    def delete(self, id: int) -> bool:
        self.validate_delete(id)
        return self.repository.delete(id)

    def validate_create(self, data: Dict) -> None:
        """Override to add create validation."""
        pass

    def validate_update(self, id: int, data: Dict) -> None:
        """Override to add update validation."""
        pass

    def validate_delete(self, id: int) -> None:
        """Override to add delete validation."""
        pass


class DomainEvent:
    """Base class for domain events."""

    def __init__(self, event_type: str, aggregate_id: int, data: Dict = None):
        self.event_type = event_type
        self.aggregate_id = aggregate_id
        self.data = data or {}

    def to_dict(self) -> Dict:
        return {
            'event_type': self.event_type,
            'aggregate_id': self.aggregate_id,
            'data': self.data,
        }


class EventBus:
    """Simple in-memory event bus for domain events."""

    _handlers = {}

    @classmethod
    def subscribe(cls, event_type: str, handler):
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)

    @classmethod
    def publish(cls, event: DomainEvent):
        handlers = cls._handlers.get(event.event_type, [])
        for handler in handlers:
            handler(event)
