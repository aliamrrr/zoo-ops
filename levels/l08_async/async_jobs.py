"""Level 08: queues, workers, retries, a dead-letter queue, and SSE streaming.

Slow work (sending emails, generating long LLM answers) leaves the request path: the API puts
a job on a queue and answers at once, workers process jobs in the background.
JobQueue mimics SQS: a message that failed comes back after a delay, and a message that
keeps failing is a poison pill that must leave the queue for a dead-letter queue (DLQ).

LLM answers stream to the browser with Server-Sent Events: a long-lived HTTP response
(Content-Type: text/event-stream) made of small text events.
"""

from __future__ import annotations

import heapq
import itertools
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

Clock = Callable[[], float]


@dataclass
class Job:
    id: str
    kind: str
    payload: dict[str, Any] = field(default_factory=dict)
    attempts: int = 0
    last_error: str | None = None


class JobQueue:
    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._heap: list[tuple[float, int, Job]] = []
        self._order = itertools.count()

    def put(self, job: Job, delay: float = 0.0) -> None:
        """The job becomes visible to workers `delay` seconds from now."""
        heapq.heappush(self._heap, (self._clock() + delay, next(self._order), job))

    def get(self) -> Job | None:
        """The oldest visible job, or None when nothing is visible yet."""
        if self._heap and self._heap[0][0] <= self._clock():
            return heapq.heappop(self._heap)[2]
        return None

    def __len__(self) -> int:
        return len(self._heap)


Handler = Callable[[dict[str, Any]], None]


class Worker:
    def __init__(
        self,
        queue: JobQueue,
        dead_letters: list[Job],
        handlers: Mapping[str, Handler],
        max_attempts: int = 3,
        retry_delay: float = 5.0,
    ) -> None:
        self.queue = queue
        self.dead_letters = dead_letters
        self.handlers = handlers
        self.max_attempts = max_attempts
        self.retry_delay = retry_delay
        self.processed: list[str] = []

    def run_once(self) -> bool:
        """Process at most one job. Return False when no job is visible, True otherwise.

        Contract:
        - success: append job.id to self.processed, nothing goes back on the queue (ack)
        - failure (the handler raised, or no handler for job.kind):
          increment job.attempts and store the error text in job.last_error
          - attempts < max_attempts: put it back with delay retry_delay * 2 ** (attempts - 1)
          - otherwise: append it to self.dead_letters and never retry it again
        - a failing job must never block the jobs behind it
        """
        # TODO(level 08)
        raise NotImplementedError("Worker.run_once")


def sse_event(data: str, event: str | None = None, event_id: str | None = None) -> str:
    """Serialize one Server-Sent Event (WHATWG HTML spec, section 9.2):
    - an optional "id: <event_id>" line, then an optional "event: <event>" line
    - one "data: <line>" line per line of `data` (a multi-line answer needs several data lines,
      the browser joins them back with newlines). A trailing newline counts:
      "a\\n" is the two lines "a" and "", which str.splitlines() would get wrong
    - every line ends with a newline and the event ends with one extra empty line

    sse_event("hello") == "data: hello\\n\\n"
    """
    # TODO(level 08)
    raise NotImplementedError("sse_event")


def parse_sse(stream: str) -> list[dict[str, str]]:
    """The browser side, simplified: split events and rebuild their fields."""
    events = []
    for block in stream.split("\n\n"):
        if not block:
            continue
        fields: dict[str, str] = {}
        data_lines = []
        for line in block.split("\n"):
            name, _, value = line.partition(":")
            value = value.removeprefix(" ")
            if name == "data":
                data_lines.append(value)
            elif name in {"event", "id"}:
                fields[name] = value
        fields["data"] = "\n".join(data_lines)
        events.append(fields)
    return events
