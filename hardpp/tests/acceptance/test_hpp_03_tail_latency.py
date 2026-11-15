"""Ticket 03: the long tail."""

import itertools
import threading
import time

import pytest

from zoo_planet.models.pool import ModelPool, ModelReplica, Overloaded


def every_tenth_is_slow() -> float:
    counter = itertools.count()

    def latency() -> float:
        return 0.3 if next(counter) % 10 == 9 else 0.01

    return latency  # type: ignore[return-value]


def test_hedging_cuts_the_tail() -> None:
    pool = ModelPool([ModelReplica(f"owl-{i}", every_tenth_is_slow()) for i in range(3)])
    durations = []
    for i in range(60):
        started = time.monotonic()
        assert pool.ask(f"question {i}")
        durations.append(time.monotonic() - started)
    durations.sort()
    assert durations[-2] < 0.12, f"p97 latency {durations[-2]:.3f}s"


def test_hedging_stays_cheap() -> None:
    replicas = [ModelReplica(f"owl-{i}", every_tenth_is_slow()) for i in range(3)]
    pool = ModelPool(replicas)
    for i in range(60):
        pool.ask(f"question {i}")
    assert sum(r.calls for r in replicas) <= 60 * 1.25, "only hedge requests that are already late"


def test_a_replica_never_runs_more_than_eight_requests_at_once() -> None:
    replicas = [ModelReplica(f"owl-{i}", lambda: 0.05) for i in range(2)]
    pool = ModelPool(replicas)
    threads = [threading.Thread(target=pool.ask, args=(f"q{i}", "high")) for i in range(40)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(10)
    assert max(r.peak_in_flight for r in replicas) <= 8
    assert sum(r.calls for r in replicas) >= 40


def test_low_priority_work_is_shed_when_saturated() -> None:
    gate = threading.Event()
    replicas = [ModelReplica(f"owl-{i}", lambda: 0.0 if gate.wait(5) else 0.0) for i in range(2)]
    pool = ModelPool(replicas)
    busy = [threading.Thread(target=pool.ask, args=(f"q{i}", "high")) for i in range(16)]
    for thread in busy:
        thread.start()
    deadline = time.monotonic() + 3
    while sum(r.in_flight for r in replicas) < 16 and time.monotonic() < deadline:
        time.sleep(0.005)
    started = time.monotonic()
    with pytest.raises(Overloaded):
        pool.ask("is the shop open?", "low")
    assert time.monotonic() - started < 0.05, "shedding must be immediate"
    waiting: list[str] = []
    vip = threading.Thread(
        target=lambda: waiting.append(pool.ask("lost child at the gate", "high"))
    )
    vip.start()
    time.sleep(0.05)
    gate.set()
    vip.join(5)
    for thread in busy:
        thread.join(5)
    assert waiting, "high priority work waits for a slot instead of failing"
