"""Ticket 05: the trace that stops at the queue."""

from collections import deque

from zoo_planet.sim import SimClock
from zoo_planet.tracing.pipeline import FeedingApi, FeedingWorker
from zoo_planet.tracing.tracer import Exporter, Tracer

INCOMING_TRACE = "4bf92f3577b34da6a3ce929d0e0e4736"
INCOMING_SPAN = "00f067aa0ba902b7"


def setup():  # type: ignore[no-untyped-def]
    clock = SimClock()
    exporter = Exporter()
    tracer = Tracer(exporter, clock)
    queue: deque = deque()  # type: ignore[type-arg]
    return (
        clock,
        exporter,
        tracer,
        FeedingApi(tracer, queue, clock),
        FeedingWorker(tracer, queue, clock),
    )


def settle(clock: SimClock, tracer: Tracer) -> None:
    clock.advance(3)
    tracer.flush()


def kept(trace_id: str) -> bool:
    return int(trace_id[:8], 16) % 100 < 5


def test_an_incoming_trace_is_continued_through_the_queue() -> None:
    clock, exporter, tracer, api, worker = setup()
    api.handle(
        {"traceparent": f"00-{INCOMING_TRACE}-{INCOMING_SPAN}-01"},
        {"animal": "Leo", "grams": 900},
        work_s=0.7,
    )
    worker.run_once()
    settle(clock, tracer)
    spans = {span.name: span for span in exporter.spans}
    assert set(spans) == {"POST /feedings", "queue.publish", "feed"}
    assert {span.context.trace_id for span in spans.values()} == {INCOMING_TRACE}
    assert spans["POST /feedings"].parent_id == INCOMING_SPAN
    assert spans["queue.publish"].parent_id == spans["POST /feedings"].context.span_id
    assert spans["feed"].parent_id == spans["queue.publish"].context.span_id


def test_every_trace_with_an_error_is_kept_whole() -> None:
    clock, exporter, tracer, api, worker = setup()
    for i in range(40):
        api.handle({}, {"animal": f"animal-{i}", "grams": 10})
        worker.run_once(fail=True)
    settle(clock, tracer)
    traces = exporter.traces()
    assert len(traces) == 40
    assert all(len(spans) == 3 for spans in traces.values())


def test_slow_traces_are_kept_and_fast_ones_sampled() -> None:
    clock, exporter, tracer, api, worker = setup()
    for i in range(200):
        api.handle({}, {"animal": f"animal-{i}", "grams": 10}, work_s=0.9 if i % 20 == 0 else 0.01)
        worker.run_once(work_s=0.01)
    settle(clock, tracer)
    traces = exporter.traces()
    slow = [
        t
        for t, spans in traces.items()
        if any(s.name == "POST /feedings" and s.end - s.start > 0.5 for s in spans)
    ]
    assert len(slow) == 10
    fast = [t for t in traces if t not in slow]
    assert all(kept(trace_id) for trace_id in fast), "fast traces follow the deterministic 5% rule"
    assert all(len(spans) == 3 for spans in traces.values()), "a trace is kept whole or not at all"


def test_nothing_is_exported_before_the_trace_is_complete() -> None:
    clock, exporter, tracer, api, worker = setup()
    api.handle({}, {"animal": "Leo", "grams": 10}, work_s=0.9)
    tracer.flush()
    assert exporter.spans == [], "the worker part of the trace is still to come"
    worker.run_once()
    settle(clock, tracer)
    assert len(exporter.spans) == 3
