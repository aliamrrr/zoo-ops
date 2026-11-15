"""Background jobs: an in-process queue (SQS in production) and the worker that drains it."""

from __future__ import annotations

import logging
from collections import deque
from collections.abc import Callable, Mapping
from typing import Any

from zoo_platform.domain.models import Job

logger = logging.getLogger("zoo.jobs")

Handler = Callable[[dict[str, Any]], None]


class JobQueue:
    def __init__(self) -> None:
        self._items: deque[Job] = deque()

    def put(self, job: Job) -> None:
        self._items.append(job)

    def take(self) -> Job | None:
        return self._items.popleft() if self._items else None

    def __len__(self) -> int:
        return len(self._items)


class Worker:
    def __init__(self, queue: JobQueue, handlers: Mapping[str, Handler]) -> None:
        self._queue = queue
        self._handlers = handlers

    def run_once(self) -> bool:
        job = self._queue.take()
        if job is None:
            return False
        try:
            self._handlers[job.kind](job.payload)
        except Exception as exc:  # noqa: BLE001 - any handler failure is a failed attempt
            job.attempts += 1
            job.last_error = f"{type(exc).__name__}: {exc}"
            logger.warning("job %s failed: %s", job.id, job.last_error)
            self._queue.put(job)
        return True

    def drain(self, max_steps: int = 10_000) -> int:
        steps = 0
        while steps < max_steps and self.run_once():
            steps += 1
        return steps
