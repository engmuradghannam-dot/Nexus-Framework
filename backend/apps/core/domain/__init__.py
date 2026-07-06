"""
DDD (Domain-Driven Design) foundation module.
Provides events, aggregates, value objects, and repositories.
"""
from .events import DomainEvent, EventBus, TenantCreated, SubscriptionUpgraded, OrderPlaced, PaymentReceived
from .aggregate import AggregateRoot, ValueObject
from .repo import Repository, DjangoRepository

__all__ = [
    'DomainEvent', 'EventBus',
    'TenantCreated', 'SubscriptionUpgraded', 'OrderPlaced', 'PaymentReceived',
    'AggregateRoot', 'ValueObject',
    'Repository', 'DjangoRepository',
]
