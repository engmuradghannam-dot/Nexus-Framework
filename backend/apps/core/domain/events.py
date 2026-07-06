"""
Domain events for DDD implementation.
Enables loose coupling between bounded contexts.
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, List, Callable
import uuid


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events."""
    event_id: str
    occurred_on: datetime
    aggregate_id: str
    event_type: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'occurred_on': self.occurred_on.isoformat(),
            'aggregate_id': self.aggregate_id,
            'event_type': self.event_type,
            'payload': asdict(self),
        }


@dataclass(frozen=True)
class TenantCreated(DomainEvent):
    """Fired when new tenant signs up."""
    tenant_name: str
    schema_name: str
    email: str
    tier: str


@dataclass(frozen=True)
class SubscriptionUpgraded(DomainEvent):
    """Fired when tenant upgrades plan."""
    old_plan: str
    new_plan: str
    amount: float


@dataclass(frozen=True)
class OrderPlaced(DomainEvent):
    """Fired when purchase/sales order is submitted."""
    order_type: str
    order_number: str
    total_amount: float
    currency: str


@dataclass(frozen=True)
class PaymentReceived(DomainEvent):
    """Fired when payment is recorded."""
    invoice_id: str
    amount: float
    payment_method: str


@dataclass(frozen=True)
class InventoryLowStock(DomainEvent):
    """Fired when inventory falls below reorder level."""
    item_id: str
    item_name: str
    warehouse_id: str
    current_quantity: float
    reorder_level: float


@dataclass(frozen=True)
class EmployeeOnboarded(DomainEvent):
    """Fired when new employee is added."""
    employee_id: str
    employee_name: str
    department: str
    email: str


class EventBus:
    """In-memory event bus. Replace with Redis/Kafka for production."""
    _handlers: Dict[str, List[Callable]] = {}

    @classmethod
    def subscribe(cls, event_type: str, handler: Callable):
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)

    @classmethod
    def unsubscribe(cls, event_type: str, handler: Callable):
        if event_type in cls._handlers:
            cls._handlers[event_type] = [h for h in cls._handlers[event_type] if h != handler]

    @classmethod
    def publish(cls, event: DomainEvent):
        handlers = cls._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Log but don't break event chain
                print(f"Event handler error: {e}")

    @classmethod
    def clear(cls):
        cls._handlers.clear()
