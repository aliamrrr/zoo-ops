"""Level 05: structured logs with a request id, latency percentiles and SLO burn-rate alerts.

- Logs: one JSON object per line, so a log backend can filter on any field. Every line carries
  the request id, so one request can be followed across services (that id is the trace id).
- Metrics: averages hide pain, percentiles show it. p95 = 95% of requests were faster.
- Alerts: page a human on the error budget burn rate, not on every blip.
"""

from __future__ import annotations

import json
import logging
import math
import time
import uuid
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


@contextmanager
def request_context(request_id: str | None = None) -> Iterator[str]:
    """Bind a request id for the duration of the block, yield it, and restore the previous
    value afterwards, even on error. Generate uuid.uuid4().hex when none is given
    (an inbound X-Request-ID header should be reused instead).
    Tip: ContextVar.set returns a token, ContextVar.reset(token) restores the previous value."""
    # TODO(level 05)
    raise NotImplementedError("request_context")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        """One JSON object per line with the keys:
        - ts: record.created as ISO 8601 in UTC (datetime.fromtimestamp(..., tz=UTC).isoformat())
        - level: record.levelname, logger: record.name, message: record.getMessage()
        - request_id: the current value of request_id_var (None outside a request)
        - every key of record.fields, when the caller passed extra={"fields": {...}}
        - exc: self.formatException(record.exc_info), only when record.exc_info is set
        """
        # TODO(level 05)
        raise NotImplementedError("JsonFormatter.format")


def percentile(values: Sequence[float], p: float) -> float:
    """Nearest-rank percentile: sort the values and return the one at 1-based rank
    ceil(p / 100 * n). p must be in (0, 100]. Empty input raises ValueError."""
    # TODO(level 05)
    raise NotImplementedError("percentile")


@dataclass(frozen=True)
class Window:
    total: int
    errors: int


def burn_rate(window: Window, slo_target: float) -> float:
    """How fast the error budget burns: error rate / (1 - slo_target).
    1.0 spends the budget exactly over the SLO period, 14.4 spends 2% of a 30-day budget in
    one hour. An empty window burns nothing (0.0)."""
    # TODO(level 05)
    raise NotImplementedError("burn_rate")


def should_page(short: Window, long: Window, slo_target: float, threshold: float = 14.4) -> bool:
    """Multiwindow burn-rate alert: page only when BOTH windows burn faster than `threshold`.
    The long window (1h) proves it matters, the short one (5m) proves it is still happening."""
    # TODO(level 05)
    raise NotImplementedError("should_page")


@contextmanager
def span(logger: logging.Logger, name: str) -> Iterator[None]:
    """A minimal tracing span: logs its duration with the request id as trace id.
    OpenTelemetry or Langfuse do the same with parent/child ids and an exporter."""
    started = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = round((time.perf_counter() - started) * 1000, 3)
        logger.info("span", extra={"fields": {"span": name, "duration_ms": duration_ms}})
