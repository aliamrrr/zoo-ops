"""A message broker with at-least-once delivery (think SQS or Kafka without transactions)."""

from __future__ import annotations

import itertools
import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    id: str
    topic: str
    body: dict[str, Any]
    deliveries: int = 0


@dataclass
class _Topic:
    ready: list[Message] = field(default_factory=list)
    unacked: dict[str, Message] = field(default_factory=dict)


class Broker:
    def __init__(self) -> None:
        self._topics: dict[str, _Topic] = {}
        self._ids = itertools.count(1)
        self._lock = threading.Lock()
        self.published: list[Message] = []

    def publish(self, topic: str, body: dict[str, Any], message_id: str | None = None) -> Message:
        message = Message(message_id or f"m-{next(self._ids)}", topic, dict(body))
        with self._lock:
            self._topics.setdefault(topic, _Topic()).ready.append(message)
            self.published.append(message)
        return message

    def receive(self, topic: str) -> Message | None:
        with self._lock:
            queue = self._topics.setdefault(topic, _Topic())
            if not queue.ready:
                return None
            message = queue.ready.pop(0)
            message.deliveries += 1
            queue.unacked[message.id] = message
            return message

    def ack(self, message: Message) -> None:
        with self._lock:
            self._topics[message.topic].unacked.pop(message.id, None)

    def redeliver_unacked(self, topic: str) -> int:
        """What happens when a consumer's visibility timeout expires."""
        with self._lock:
            queue = self._topics.setdefault(topic, _Topic())
            pending = list(queue.unacked.values())
            queue.unacked.clear()
            queue.ready[:0] = pending
            return len(pending)
