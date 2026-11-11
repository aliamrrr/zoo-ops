from typing import Any

import pytest

from levels.l08_async.async_jobs import Job, JobQueue, Worker, parse_sse, sse_event
from zoo.kit import FakeClock


class Flaky:
    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.calls = 0

    def __call__(self, payload: dict[str, Any]) -> None:
        self.calls += 1
        if self.calls <= self.failures:
            raise ConnectionError(f"failure {self.calls}")


def rotten(payload: dict[str, Any]) -> None:
    raise ValueError("rotten leaf")


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


def make_worker(clock: FakeClock, **handlers: Any) -> tuple[JobQueue, Worker, list[Job]]:
    queue, dead = JobQueue(clock), []
    return queue, Worker(queue, dead, handlers, max_attempts=3, retry_delay=5.0), dead


def test_empty_queue_returns_false(clock: FakeClock) -> None:
    _, worker, _ = make_worker(clock)
    assert worker.run_once() is False


def test_success_acks_the_job(clock: FakeClock) -> None:
    queue, worker, dead = make_worker(clock, carry=lambda payload: None)
    queue.put(Job("j1", "carry"))
    assert worker.run_once() is True
    assert worker.processed == ["j1"]
    assert len(queue) == 0 and dead == []


def test_failure_is_retried_with_backoff(clock: FakeClock) -> None:
    flaky = Flaky(failures=2)
    queue, worker, dead = make_worker(clock, carry=flaky)
    job = Job("j1", "carry")
    queue.put(job)
    worker.run_once()
    assert job.attempts == 1 and "failure 1" in str(job.last_error)
    assert worker.run_once() is False, "the retry must wait for its delay"
    clock.advance(5)
    worker.run_once()
    assert job.attempts == 2
    clock.advance(9.9)
    assert worker.run_once() is False, "second retry waits retry_delay * 2"
    clock.advance(0.1)
    worker.run_once()
    assert worker.processed == ["j1"] and dead == []


def test_poison_job_goes_to_the_dead_letter_queue(clock: FakeClock) -> None:
    queue, worker, dead = make_worker(clock, rot=rotten)
    queue.put(Job("poison", "rot"))
    for _ in range(10):
        worker.run_once()
        clock.advance(60)
    assert [job.id for job in dead] == ["poison"]
    assert dead[0].attempts == 3
    assert "rotten leaf" in str(dead[0].last_error)
    assert len(queue) == 0


def test_unknown_kind_is_a_failure(clock: FakeClock) -> None:
    queue, worker, dead = make_worker(clock)
    queue.put(Job("j1", "teleport"))
    worker.run_once()
    assert len(queue) == 1 and queue.get() is None
    clock.advance(1_000)
    worker.run_once()
    worker.run_once()
    clock.advance(1_000)
    worker.run_once()
    assert [job.id for job in dead] == ["j1"]


def test_poison_job_does_not_block_others(clock: FakeClock) -> None:
    queue, worker, _ = make_worker(clock, rot=rotten, carry=lambda payload: None)
    queue.put(Job("poison", "rot"))
    queue.put(Job("seed", "carry"))
    worker.run_once()
    worker.run_once()
    assert worker.processed == ["seed"]


def test_sse_single_line() -> None:
    assert sse_event("hello") == "data: hello\n\n"


def test_sse_with_event_and_id() -> None:
    raw = sse_event("hoot", event="token", event_id="7")
    assert raw.endswith("\n\n") and raw.count("\n\n") == 1
    assert parse_sse(raw) == [{"id": "7", "event": "token", "data": "hoot"}]


def test_sse_multi_line_data() -> None:
    raw = sse_event("line one\nline two")
    assert raw == "data: line one\ndata: line two\n\n"
    assert parse_sse(raw)[0]["data"] == "line one\nline two"


def test_sse_stream_round_trip() -> None:
    words = ["Otters ", "hold ", "hands.\n", "Cute!"]
    stream = "".join(sse_event(word, event="token") for word in words)
    assert "".join(event["data"] for event in parse_sse(stream)) == "".join(words)
