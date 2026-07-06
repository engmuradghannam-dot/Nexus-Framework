"""
Base aggregate root for DDD.
"""
from abc import ABC, abstractmethod
from typing import List
from .events import DomainEvent


class AggregateRoot(ABC):
    """Base class for aggregate roots."""

    def __init__(self):
        self._events: List[DomainEvent] = []
        self._version = 0

    def apply_event(self, event: DomainEvent):
        """Apply event to mutate state."""
        self._events.append(event)
        self._handle(event)
        self._version += 1

    @abstractmethod
    def _handle(self, event: DomainEvent):
        """Handle specific event types."""
        pass

    def get_uncommitted_events(self) -> List[DomainEvent]:
        """Get events not yet persisted."""
        return self._events[:]

    def mark_committed(self):
        """Clear events after persistence."""
        self._events.clear()

    @property
    def version(self):
        return self._version


class ValueObject(ABC):
    """Base class for value objects (immutable, no identity)."""

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))
