"""The edge: gateway replicas in several regions, and the shared store they can all reach."""

from __future__ import annotations

import threading
from collections import defaultdict
from typing import Any

from zoo_planet.sim import Clock

LIMIT_PER_MINUTE = 100


class SharedStore:
    """A strongly consistent key-value store reachable from every region (think DynamoDB).

    Every value carries a version. Writes can be conditional on it. The store has its own,
    authoritative clock, exposed by `now()`.
    """

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._data: dict[str, tuple[Any, int]] = {}
        self._lock = threading.Lock()
        self.operations = 0

    def now(self) -> float:
        return self._clock()

    def get(self, key: str) -> tuple[Any | None, int]:
        with self._lock:
            self.operations += 1
            return self._data.get(key, (None, 0))

    def compare_and_set(self, key: str, expected_version: int, value: Any) -> bool:
        with self._lock:
            self.operations += 1
            _, version = self._data.get(key, (None, 0))
            if version != expected_version:
                return False
            self._data[key] = (value, version + 1)
            return True


class Gateway:
    def __init__(self, region: str, store: SharedStore, local_clock: Clock) -> None:
        self.region = region
        self._store = store
        self._clock = local_clock
        self._counts: defaultdict[tuple[str, int], int] = defaultdict(int)
        self._lock = threading.Lock()

    def admit(self, caller: str) -> bool:
        window = int(self._clock() // 60)
        with self._lock:
            self._counts[(caller, window)] += 1
            return self._counts[(caller, window)] <= LIMIT_PER_MINUTE
