"""The Owl model fleet: several replicas of the same model behind one pool."""

from __future__ import annotations

import random
import threading
import time
from collections.abc import Callable


class Overloaded(Exception):
    """The pool refused the request to protect itself."""


class ModelReplica:
    def __init__(self, name: str, latency_s: Callable[[], float]) -> None:
        self.name = name
        self._latency_s = latency_s
        self._lock = threading.Lock()
        self.calls = 0
        self.in_flight = 0
        self.peak_in_flight = 0

    def ask(self, prompt: str) -> str:
        with self._lock:
            self.calls += 1
            self.in_flight += 1
            self.peak_in_flight = max(self.peak_in_flight, self.in_flight)
        try:
            time.sleep(self._latency_s())
            return f"{self.name}: hoot about {prompt}"
        finally:
            with self._lock:
                self.in_flight -= 1


class ModelPool:
    def __init__(self, replicas: list[ModelReplica], rng: random.Random | None = None) -> None:
        self.replicas = replicas
        self._rng = rng or random.Random(7)

    def ask(self, prompt: str, priority: str = "normal") -> str:
        return self._rng.choice(self.replicas).ask(prompt)
