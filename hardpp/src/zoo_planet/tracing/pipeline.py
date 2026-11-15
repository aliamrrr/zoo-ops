"""The feeding pipeline: an API that accepts feeding requests and a worker that runs them."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from zoo_planet.sim import SimClock
from zoo_planet.tracing.tracer import Tracer


@dataclass
class Job:
    animal: str
    grams: int
    headers: dict[str, str] = field(default_factory=dict)


class FeedingApi:
    def __init__(self, tracer: Tracer, queue: deque[Job], clock: SimClock) -> None:
        self._tracer = tracer
        self._queue = queue
        self._clock = clock

    def handle(
        self, headers: Mapping[str, str], body: Mapping[str, Any], work_s: float = 0.02
    ) -> None:
        span = self._tracer.start("POST /feedings")
        self._clock.advance(work_s)
        publish = self._tracer.start("queue.publish", span.context)
        self._queue.append(Job(str(body["animal"]), int(body["grams"])))
        self._tracer.finish(publish)
        self._tracer.finish(span)


class FeedingWorker:
    def __init__(self, tracer: Tracer, queue: deque[Job], clock: SimClock) -> None:
        self._tracer = tracer
        self._queue = queue
        self._clock = clock

    def run_once(self, work_s: float = 0.05, fail: bool = False) -> bool:
        if not self._queue:
            return False
        job = self._queue.popleft()
        span = self._tracer.start("feed")
        span.attributes["animal"] = job.animal
        self._clock.advance(work_s)
        self._tracer.finish(span, error=fail)
        return True
