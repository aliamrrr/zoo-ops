"""Scene 08: the ant colony carries seeds. Some leaves are rotten. The Owl streams live."""

from __future__ import annotations

from typing import Any

from levels.l08_async.async_jobs import Job, JobQueue, Worker, parse_sse, sse_event
from zoo.kit import FakeClock, Scene

MAX_TICKS = 2_000


def play(scene: Scene) -> None:
    clock = FakeClock()
    queue, dead = JobQueue(clock), []
    sore_backs = {"seed-7": 2}

    def carry(payload: dict[str, Any]) -> None:
        remaining = sore_backs.get(payload["seed"], 0)
        if remaining:
            sore_backs[payload["seed"]] = remaining - 1
            raise TimeoutError("ant dropped the seed")

    def rot(payload: dict[str, Any]) -> None:
        raise ValueError(f"leaf {payload['leaf']} is rotten")

    worker = Worker(queue, dead, {"carry": carry, "rot": rot}, max_attempts=3, retry_delay=2.0)
    jobs = [Job(f"seed-{i}", "carry", {"seed": f"seed-{i}"}) for i in range(30)]
    jobs.insert(3, Job("leaf-a", "rot", {"leaf": "a"}))
    jobs.insert(17, Job("leaf-b", "rot", {"leaf": "b"}))
    for job in jobs:
        queue.put(job)

    ticks = 0
    while len(queue) and ticks < MAX_TICKS:
        if not worker.run_once():
            clock.advance(1)
        ticks += 1

    scene.info(f"{len(jobs)} jobs queued: 30 seeds, 2 rotten leaves, one clumsy ant on seed-7.")
    scene.metric("delivered", len(worker.processed))
    scene.metric("dead letters", ", ".join(job.id for job in dead) or "none")
    scene.metric("worker ticks", ticks)
    scene.check(
        ticks < MAX_TICKS,
        "The queue drained: no job loops forever.",
        "The colony is stuck: a poison job is retried forever.",
    )
    scene.check(
        len(worker.processed) == 30 and "seed-7" in worker.processed,
        "All 30 seeds delivered, seed-7 made it on its third try.",
        f"Only {len(worker.processed)} of 30 seeds were delivered.",
    )
    scene.check(
        sorted(job.id for job in dead) == ["leaf-a", "leaf-b"]
        and all(job.last_error for job in dead),
        "Rotten leaves sit in the lost and found (DLQ) with their error, ready to inspect.",
        "Rotten leaves were not quarantined in the dead-letter queue.",
    )

    answer = [
        "Otters ",
        "hold ",
        "hands ",
        "while ",
        "sleeping.\n",
        "So ",
        "they ",
        "never ",
        "drift ",
        "apart.",
    ]
    stream = "".join(
        sse_event(word, event="token", event_id=str(i)) for i, word in enumerate(answer)
    )
    events = parse_sse(stream)
    rebuilt = "".join(event["data"] for event in events)
    scene.metric("sse events", len(events))
    scene.check(
        rebuilt == "".join(answer) and all(event.get("event") == "token" for event in events),
        "The Owl's answer streams word by word over SSE, line breaks included.",
        "The SSE stream is garbled: the browser cannot rebuild the Owl's answer.",
    )
