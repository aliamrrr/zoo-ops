"""Tracing: spans, a tracer, and the exporter that ships them to the tracing backend."""

from __future__ import annotations

import random
import secrets
import threading
from dataclasses import dataclass, field
from typing import Any

from zoo_planet.sim import Clock


@dataclass(frozen=True, slots=True)
class SpanContext:
    trace_id: str
    span_id: str
    sampled: bool = True


@dataclass(slots=True)
class Span:
    name: str
    context: SpanContext
    parent_id: str | None
    start: float
    end: float | None = None
    error: bool = False
    attributes: dict[str, Any] = field(default_factory=dict)


class Exporter:
    """The tracing backend. Everything here costs money to store."""

    def __init__(self) -> None:
        self.spans: list[Span] = []
        self._lock = threading.Lock()

    def export(self, spans: list[Span]) -> None:
        with self._lock:
            self.spans.extend(spans)

    def traces(self) -> dict[str, list[Span]]:
        grouped: dict[str, list[Span]] = {}
        for span in self.spans:
            grouped.setdefault(span.context.trace_id, []).append(span)
        return grouped


class Tracer:
    def __init__(
        self,
        exporter: Exporter,
        clock: Clock,
        sample_rate: float = 0.1,
        rng: random.Random | None = None,
    ) -> None:
        self._exporter = exporter
        self._clock = clock
        self._sample_rate = sample_rate
        self._rng = rng or random.Random(5)

    def start(self, name: str, parent: SpanContext | None = None) -> Span:
        if parent is None:
            context = SpanContext(
                secrets.token_hex(16),
                secrets.token_hex(8),
                sampled=self._rng.random() < self._sample_rate,
            )
        else:
            context = SpanContext(parent.trace_id, secrets.token_hex(8), parent.sampled)
        return Span(name, context, parent.span_id if parent else None, self._clock())

    def finish(self, span: Span, error: bool = False) -> None:
        span.end = self._clock()
        span.error = error
        if span.context.sampled:
            self._exporter.export([span])

    def flush(self) -> None:
        """Called periodically by the collector loop."""
