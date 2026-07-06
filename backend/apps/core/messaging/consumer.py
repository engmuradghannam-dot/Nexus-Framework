"""
Event consumer for microservices.
Processes events from message broker.
"""
import json
import threading
from typing import Dict, Any, Callable, List
from .publisher import RedisBroker, InMemoryBroker


class EventConsumer:
    """Background event consumer for async processing."""

    def __init__(self, broker=None):
        self._broker = broker or InMemoryBroker()
        self._handlers: Dict[str, List[Callable]] = {}
        self._running = False
        self._thread = None

    def register(self, event_type: str, handler: Callable):
        """Register handler for event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

        # Subscribe to broker topic
        topic = f"nexus.events.{event_type}"
        self._broker.subscribe(topic, lambda msg: self._process_message(msg))

    def _process_message(self, message: Dict[str, Any]):
        """Process incoming message."""
        event_type = message.get('event_type')
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(message['payload'], message.get('tenant_id'))
            except Exception as e:
                print(f"Consumer handler error: {e}")

    def start(self):
        """Start consumer in background thread."""
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        """Main consumer loop."""
        while self._running:
            try:
                # For Redis, this would be a blocking listen
                # For in-memory, events are pushed directly
                import time
                time.sleep(0.1)
            except Exception as e:
                print(f"Consumer loop error: {e}")

    def stop(self):
        """Stop consumer."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
