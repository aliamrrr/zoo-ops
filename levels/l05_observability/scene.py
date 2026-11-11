"""Scene 05: an hour of zoo traffic. The sloth exhibit is slow and an incident starts at the end."""

from __future__ import annotations

import io
import json
import logging
import random

from levels.l05_observability.observability import (
    JsonFormatter,
    Window,
    percentile,
    request_context,
    should_page,
    span,
)
from zoo.kit import Scene

SLO_TARGET = 0.999
PATHS = ["/lion", "/zebra", "/otter", "/sloth"]


def play(scene: Scene) -> None:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("zoo.lookout")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)

    rng = random.Random(5)
    latencies: list[float] = []
    sloth_latencies: list[float] = []
    minutes: list[tuple[int, bool]] = []
    failing_id = ""

    for i in range(600):
        minute = i // 10
        path = rng.choice(PATHS)
        latency = rng.uniform(900, 1500) if path == "/sloth" else rng.uniform(20, 120)
        incident = minute >= 55
        failed = incident and rng.random() < 0.4
        with request_context() as rid, span(logger, f"GET {path}"):
            fields = {"path": path, "latency_ms": round(latency), "status": 500 if failed else 200}
            if failed:
                failing_id = failing_id or rid
                logger.error("enclosure database unreachable", extra={"fields": fields})
            else:
                logger.info("served", extra={"fields": fields})
        latencies.append(latency)
        if path == "/sloth":
            sloth_latencies.append(latency)
        minutes.append((minute, failed))

    records = [json.loads(line) for line in stream.getvalue().splitlines()]
    with_ids = [r for r in records if r.get("request_id")]
    scene.info(f"600 requests in one hour, {len(records)} JSON log lines collected.")
    scene.check(
        len(with_ids) == len(records) == 1200,
        "Every log line is JSON with its request id.",
        f"Only {len(with_ids)} of {len(records)} log lines carry a request id.",
    )
    trail = [r for r in records if r.get("request_id") == failing_id]
    scene.check(
        len(trail) == 2
        and {r.get("message") for r in trail} == {"enclosure database unreachable", "span"},
        f"Filtering on request_id={failing_id[:8]} shows the full story of the first failure.",
        "Mika cannot follow the failing request: its log lines are not linked by request id.",
    )

    p50, p95 = percentile(latencies, 50), percentile(latencies, 95)
    scene.metric("p50", f"{p50:.0f} ms")
    scene.metric("p95", f"{p95:.0f} ms")
    scene.metric("sloth p50", f"{percentile(sloth_latencies, 50):.0f} ms")
    scene.check(
        p50 < 150 < 900 < p95,
        f"The average looks fine but p95 = {p95:.0f} ms reveals the slow sloth path.",
        f"Percentiles are off: p50 = {p50:.0f} ms, p95 = {p95:.0f} ms.",
    )

    def window(first_minute: int) -> Window:
        sample = [failed for minute, failed in minutes if minute >= first_minute]
        return Window(total=len(sample), errors=sum(sample))

    paged = should_page(short=window(55), long=window(0), slo_target=SLO_TARGET)
    scene.metric("errors last 5 min", window(55).errors)
    scene.check(
        paged,
        "Both burn-rate windows are on fire: Mika pages the on-call keeper.",
        "The enclosure database is down and nobody got paged.",
    )
    blip = [False] * 3590 + [True] * 10
    blip_page = should_page(
        short=Window(60, 10), long=Window(len(blip), sum(blip)), slo_target=0.99
    )
    scene.check(
        not blip_page,
        "A 10-error blip yesterday did not wake anyone up.",
        "A tiny blip paged the keeper at 3 am. Alert fatigue incoming.",
    )
