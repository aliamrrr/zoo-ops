"""Simulation primitives shared by every subsystem: a controllable clock and crash injection."""

from __future__ import annotations

import threading
from collections.abc import Callable

Clock = Callable[[], float]


class SimClock:
    """Simulated time. Nothing moves unless someone advances it."""

    def __init__(self, start: float = 1_700_000_000.0) -> None:
        self._now = start
        self._lock = threading.Lock()

    def __call__(self) -> float:
        with self._lock:
            return self._now

    def advance(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("time only moves forward")
        with self._lock:
            self._now += seconds

    def skewed(self, offset_s: float) -> Clock:
        """The same clock seen by a machine whose clock is off by `offset_s`."""
        return lambda: self() + offset_s


class Crash(Exception):
    """The process died at a crash point. Nothing after it ran."""


class CrashPlan:
    """Named crash points. Components call `point(name)`; tests arm the ones they want to fail."""

    def __init__(self) -> None:
        self._armed: dict[str, int] = {}
        self.hits: list[str] = []

    def arm(self, name: str, times: int = 1) -> None:
        self._armed[name] = times

    def point(self, name: str) -> None:
        self.hits.append(name)
        remaining = self._armed.get(name, 0)
        if remaining:
            self._armed[name] = remaining - 1
            raise Crash(name)
