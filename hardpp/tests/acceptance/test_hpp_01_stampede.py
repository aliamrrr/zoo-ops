"""Ticket 01: the viral question."""

import threading
import time

from zoo_planet.cache.nodes import AnswerService, CacheCluster, CacheNode
from zoo_planet.sim import SimClock


class SlowModel:
    def __init__(self, delay_s: float = 0.05) -> None:
        self.calls: list[str] = []
        self.delay_s = delay_s
        self.gate: threading.Event | None = None
        self.version = 1
        self._lock = threading.Lock()

    def __call__(self, question: str) -> str:
        with self._lock:
            self.calls.append(question)
        if self.gate is not None:
            self.gate.wait(5)
        time.sleep(self.delay_s)
        return f"answer v{self.version} to {question}"


def cluster(clock: SimClock, size: int = 3) -> CacheCluster:
    return CacheCluster(CacheNode(f"node-{i}", clock) for i in range(size))


def burst(service: AnswerService, question: str, count: int) -> list[str]:
    results: list[str] = []
    barrier = threading.Barrier(count)

    def visitor() -> None:
        barrier.wait()
        results.append(service.answer(question))

    threads = [threading.Thread(target=visitor) for _ in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(10)
    return results


def test_a_viral_miss_calls_the_model_once() -> None:
    clock, model = SimClock(), SlowModel()
    service = AnswerService(cluster(clock), model, ttl_s=60)
    results = burst(service, "why are flamingos pink?", 40)
    assert len(results) == 40
    assert len(model.calls) == 1
    assert set(results) == {"answer v1 to why are flamingos pink?"}


def test_coalescing_is_per_question() -> None:
    clock, model = SimClock(), SlowModel()
    service = AnswerService(cluster(clock), model, ttl_s=60)
    threads = [threading.Thread(target=burst, args=(service, q, 10)) for q in ("otters?", "lions?")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(10)
    assert sorted(model.calls) == ["lions?", "otters?"]


def test_an_expired_hot_answer_is_refreshed_once_while_visitors_get_the_stale_one() -> None:
    clock, model = SimClock(), SlowModel(delay_s=0.0)
    service = AnswerService(cluster(clock), model, ttl_s=60)
    service.answer("why are flamingos pink?")
    model.version = 2
    model.gate = threading.Event()
    clock.advance(61)
    started = time.monotonic()
    results = burst(service, "why are flamingos pink?", 20)
    waited = time.monotonic() - started
    assert set(results) == {
        "answer v1 to why are flamingos pink?"
    }, "serve the stale answer during the refresh"
    assert waited < 1.0, "visitors must not wait for the refresh"
    model.gate.set()
    deadline = time.monotonic() + 3
    while (
        service.answer("why are flamingos pink?").startswith("answer v1")
        and time.monotonic() < deadline
    ):
        time.sleep(0.01)
    assert service.answer("why are flamingos pink?") == "answer v2 to why are flamingos pink?"
    assert len(model.calls) == 2


def test_very_old_answers_are_not_served() -> None:
    clock, model = SimClock(), SlowModel(delay_s=0.0)
    service = AnswerService(cluster(clock), model, ttl_s=60)
    service.answer("otters?")
    model.version = 2
    clock.advance(60 + 120)
    assert service.answer("otters?") == "answer v2 to otters?"


def test_adding_a_node_moves_few_keys() -> None:
    clock = SimClock()
    ring = cluster(clock, 3)
    keys = [f"question-{i}" for i in range(3_000)]
    before = {key: ring.node_for(key).name for key in keys}
    ring.add_node(CacheNode("node-3", clock))
    after = {key: ring.node_for(key).name for key in keys}
    moved = sum(before[key] != after[key] for key in keys) / len(keys)
    assert moved <= 0.35, f"{moved:.0%} of the keys moved"
    assert all(
        after[key] in (before[key], "node-3") for key in keys
    ), "keys only move to the new node"


def test_keys_are_spread_evenly() -> None:
    clock = SimClock()
    ring = cluster(clock, 4)
    counts: dict[str, int] = {}
    for i in range(8_000):
        name = ring.node_for(f"question-{i}").name
        counts[name] = counts.get(name, 0) + 1
    assert all(1_200 <= count <= 2_800 for count in counts.values()), counts
