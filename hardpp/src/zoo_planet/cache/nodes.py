"""The answer cache: a cluster of cache nodes in front of the Owl models."""

from __future__ import annotations

import threading
import zlib
from collections.abc import Callable, Iterable
from typing import Any

from zoo_planet.sim import Clock


class CacheNode:
    def __init__(self, name: str, clock: Clock) -> None:
        self.name = name
        self._clock = clock
        self._data: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._data.get(key)
        if entry is None or entry[1] <= self._clock():
            return None
        return entry[0]

    def get_entry(self, key: str) -> tuple[Any, float] | None:
        """The stored value and its expiry time, even when already expired."""
        with self._lock:
            return self._data.get(key)

    def set(self, key: str, value: Any, ttl_s: float) -> None:
        with self._lock:
            self._data[key] = (value, self._clock() + ttl_s)

    def keys(self) -> list[str]:
        with self._lock:
            return list(self._data)


class CacheCluster:
    def __init__(self, nodes: Iterable[CacheNode]) -> None:
        self.nodes = list(nodes)

    def node_for(self, key: str) -> CacheNode:
        return self.nodes[zlib.crc32(key.encode()) % len(self.nodes)]

    def add_node(self, node: CacheNode) -> None:
        self.nodes.append(node)


Model = Callable[[str], str]


class AnswerService:
    """Answers questions from the cache, asking the model on a miss."""

    def __init__(self, cluster: CacheCluster, model: Model, ttl_s: float = 60.0) -> None:
        self._cluster = cluster
        self._model = model
        self._ttl_s = ttl_s

    def answer(self, question: str) -> str:
        node = self._cluster.node_for(question)
        cached = node.get(question)
        if cached is not None:
            return str(cached)
        value = self._model(question)
        node.set(question, value, self._ttl_s)
        return value
