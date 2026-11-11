"""Level 10: canary releases, automatic rollback, health checks and graceful shutdown.

A stateless app (no session in memory, everything in Redis or the database) can be killed,
cloned and rescheduled at any time. That is what makes autoscaling and rolling deploys safe,
provided each instance:
    - answers liveness (am I stuck?) and readiness (should I get traffic?) separately
    - on SIGTERM stops being ready, finishes in-flight requests, then exits
A canary release sends a small, sticky share of users to the new version and compares it
with the baseline before going further.
"""

from __future__ import annotations

import hashlib
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Literal

Verdict = Literal["wait", "promote", "rollback"]


def in_canary(user_id: str, percent: float) -> bool:
    """Sticky routing: a user always lands on the same side, across processes and restarts.

    Contract:
    - hash user_id with sha256 (never the built-in hash(): it is salted per process)
    - take the first 8 bytes of the digest as a big-endian integer, bucket = that % 100
    - return bucket < percent (0 sends nobody, 100 sends everybody)
    """
    # TODO(level 10)
    raise NotImplementedError("in_canary")


@dataclass(frozen=True)
class ReleaseStats:
    requests: int
    errors: int
    p95_ms: float

    @property
    def error_rate(self) -> float:
        return self.errors / self.requests if self.requests else 0.0


def judge_canary(
    baseline: ReleaseStats,
    canary: ReleaseStats,
    min_requests: int = 200,
    max_error_delta: float = 0.01,
    max_latency_ratio: float = 1.25,
) -> Verdict:
    """Decide what to do with a canary, checked in this order:
    - fewer than `min_requests` canary requests: "wait", not enough evidence yet
    - canary error rate > baseline error rate + max_error_delta: "rollback"
    - canary p95 > baseline p95 * max_latency_ratio: "rollback"
    - otherwise: "promote"
    """
    # TODO(level 10)
    raise NotImplementedError("judge_canary")


class ShuttingDown(Exception):
    """New request refused while draining (HTTP 503, the load balancer retries elsewhere)."""


class Lifecycle:
    """Health and shutdown state of one instance, shared by all request threads."""

    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._in_flight = 0
        self._draining = False

    @property
    def in_flight(self) -> int:
        with self._cond:
            return self._in_flight

    def live(self) -> bool:
        """Liveness: the process answers. Keep it dumb, a failing liveness probe restarts us."""
        return True

    def ready(self) -> bool:
        """Readiness: True until shutdown begins."""
        # TODO(level 10)
        raise NotImplementedError("Lifecycle.ready")

    @contextmanager
    def track_request(self) -> Iterator[None]:
        """Wrap the handling of one request.
        - draining: raise ShuttingDown without counting the request
        - otherwise count it as in flight for the duration of the block, and always uncount
          it at the end (even on error), notifying threads waiting for the drain
        Use self._cond as the lock around every read and write of the counters."""
        # TODO(level 10)
        raise NotImplementedError("Lifecycle.track_request")

    def begin_shutdown(self) -> None:
        """Called on SIGTERM: stop being ready, refuse new requests."""
        # TODO(level 10)
        raise NotImplementedError("Lifecycle.begin_shutdown")

    def wait_until_drained(self, timeout: float) -> bool:
        """Block until no request is in flight or `timeout` elapses, return True when drained.
        Tip: Condition.wait_for(predicate, timeout)."""
        # TODO(level 10)
        raise NotImplementedError("Lifecycle.wait_until_drained")
