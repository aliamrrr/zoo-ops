"""Ticket 05: flying blind."""

import itertools
import json

from zp_testkit import World, ask, auth

_counter = itertools.count()


def question() -> str:
    return f"Tell me about otters, visit {next(_counter)}"


def log_lines(world: World) -> list[dict]:  # type: ignore[type-arg]
    return [json.loads(line) for line in world.logs.getvalue().splitlines() if line.strip()]


def test_every_log_line_is_json(world: World) -> None:
    world.client.get("/v1/animals", params={"species": "cat"}, headers=auth())
    ask(world.client, question())
    lines = log_lines(world)
    assert lines
    assert all({"ts", "level", "logger", "message"} <= line.keys() for line in lines)


def test_the_request_id_is_echoed_and_logged(world: World) -> None:
    response = ask(world.client, question(), headers={"X-Request-ID": "req-otter-42"})
    assert response.headers["X-Request-ID"] == "req-otter-42"
    tagged = [line for line in log_lines(world) if line.get("request_id") == "req-otter-42"]
    assert len({line["logger"] for line in tagged}) >= 2, "the service logs must carry it too"


def test_a_request_id_is_created_when_missing(world: World) -> None:
    first = ask(world.client, question()).headers.get("X-Request-ID")
    second = ask(world.client, question()).headers.get("X-Request-ID")
    assert first and second and first != second


def test_metrics_show_the_p95_per_route(world: World) -> None:
    for i in range(20):
        world.owl.latency_s = 1.2 if i % 10 == 0 else 0.05
        ask(world.client, question(), user=f"visitor-{i}")
    route = world.client.get("/internal/metrics").json()["routes"]["POST /v1/owl/answers"]
    assert route["count"] == 20
    assert 1_150 <= route["p95_ms"] <= 1_250


def test_metrics_count_server_errors(world: World) -> None:
    world.owl.outage = world.parrot.outage = True
    for i in range(3):
        ask(world.client, question(), user=f"visitor-{i}")
    assert (
        world.client.get("/internal/metrics").json()["routes"]["POST /v1/owl/answers"]["errors"]
        == 3
    )


def traffic(world: World, good: int, spacing_s: float) -> None:
    for i in range(good):
        ask(world.client, question(), user=f"visitor-{i % 10}")
        world.clock.advance(spacing_s)


def failures(world: World, count: int) -> None:
    world.owl.outage = world.parrot.outage = True
    for i in range(count):
        ask(world.client, question(), user=f"visitor-{i % 10}")
        world.clock.advance(1)
    world.owl.outage = world.parrot.outage = False


def test_a_fast_burn_pages_the_keeper(world: World) -> None:
    traffic(world, 150, spacing_s=22)
    failures(world, 30)
    alert = world.client.get("/internal/alerts").json()
    assert alert["page"] is True
    assert alert["burn_rate_short"] > 14.4 and alert["burn_rate_long"] > 14.4


def test_an_old_blip_does_not_page(world: World) -> None:
    failures(world, 30)
    traffic(world, 150, spacing_s=22)
    assert world.client.get("/internal/alerts").json()["page"] is False
