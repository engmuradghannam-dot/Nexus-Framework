"""
Event publisher for microservices communication.
Supports both sync (in-memory) and async (Redis/RabbitMQ) modes.
"""
import json
import redis
from django.conf import settings
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class MessageBroker(ABC):
    @abstractmethod
    def publish(self, topic: str, message: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def subscribe(self, topic: str, handler):
        pass

    @abstractmethod
    def close(self):
        pass


class RedisBroker(MessageBroker):
    """Redis pub/sub implementation."""

    def __init__(self, redis_url: Optional[str] = None):
        self._redis_url = redis_url or getattr(settings, 'REDIS_URL', 'redis://redis:6379/0')
        self._redis = redis.from_url(self._redis_url)
        self._pubsub = self._redis.pubsub()
        self._handlers = {}

    def publish(self, topic: str, message: Dict[str, Any]) -> bool:
        try:
            self._redis.publish(topic, json.dumps(message))
            return True
        except Exception as e:
            print(f"Redis publish error: {e}")
            return False

    def subscribe(self, topic: str, handler):
        self._handlers[topic] = handler
        self._pubsub.subscribe(**{topic: self._on_message})

    def _on_message(self, message):
        if message['type'] == 'message':
            topic = message['channel'].decode()
            data = json.loads(message['data'])
            handler = self._handlers.get(topic)
            if handler:
                handler(data)

    def close(self):
        self._pubsub.close()
        self._redis.close()


class InMemoryBroker(MessageBroker):
    """For development/testing."""

    def __init__(self):
        self._handlers = {}

    def publish(self, topic: str, message: Dict[str, Any]) -> bool:
        handlers = self._handlers.get(topic, [])
        for handler in handlers:
            try:
                handler(message)
            except Exception as e:
                print(f"Handler error: {e}")
        return True

    def subscribe(self, topic: str, handler):
        if topic not in self._handlers:
            self._handlers[topic] = []
        self._handlers[topic].append(handler)

    def close(self):
        pass


class EventPublisher:
    """Facade for publishing domain events across services."""

    def __init__(self, broker: Optional[MessageBroker] = None):
        if broker is None:
            if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
                broker = RedisBroker()
            else:
                broker = InMemoryBroker()
        self._broker = broker

    def publish(self, event_type: str, payload: Dict[str, Any], tenant_id: str = None):
        message = {
            'event_type': event_type,
            'payload': payload,
            'tenant_id': tenant_id,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
            'source': 'nexus-erp',
        }
        topic = f"nexus.events.{event_type}"
        return self._broker.publish(topic, message)

    def publish_tenant_event(self, tenant_id: str, event_type: str, payload: Dict[str, Any]):
        """Publish event scoped to specific tenant."""
        return self.publish(event_type, payload, tenant_id)

    def close(self):
        self._broker.close()
