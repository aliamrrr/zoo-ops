"""Ticket 10: release day."""

import hashlib
import itertools
import threading
import time

from zp_testkit import World, ask

_counter = itertools.count()


def question() -> str:
    return f"Tell me about otters, round {next(_counter)}"


def test_draining_flips_readiness_but_not_liveness(world: World) -> None:
    assert world.client.post("/internal/lifecycle/drain").status_code == 202
    assert world.client.get("/readyz").status_code == 503
    assert world.client.get("/healthz").status_code == 200


def test_new_requests_are_refused_while_draining(world: World) -> None:
    world.client.post("/internal/lifecycle/drain")
    refused = ask(world.client, question())
    assert refused.status_code == 503
    assert "Retry-After" in refused.headers


def test_in_flight_requests_finish_during_a_drain(world: World) -> None:
    world.owl.gate = threading.Event()
    result: list[int] = []
    slow = threading.Thread(target=lambda: result.append(ask(world.client, question()).status_code))
    slow.start()
    deadline = time.time() + 5
    while not world.owl.requests and time.time() < deadline:
        time.sleep(0.01)
    world.client.post("/internal/lifecycle/drain")
    assert world.client.get("/internal/lifecycle").json() == {"draining": True, "in_flight": 1}
    world.owl.gate.set()
    slow.join(5)
    assert result == [200]
    assert world.client.get("/internal/lifecycle").json() == {"draining": True, "in_flight": 0}


def canary_bucket(user: str) -> int:
    return int(hashlib.sha256(user.encode()).hexdigest()[:16], 16) % 100


def test_canary_users_are_chosen_by_a_stable_hash(make_world) -> None:  # type: ignore[no-untyped-def]
    world = make_world(canary_percent=10.0)
    users = [f"visitor-{i}" for i in range(120)]
    for user in users:
        release = ask(world.client, question(), user=user).headers["X-Release"]
        assert release == ("canary" if canary_bucket(user) < 10 else "stable"), user


def test_the_canary_runs_the_new_model(make_world) -> None:  # type: ignore[no-untyped-def]
    world = make_world(canary_percent=10.0)
    canary_user = next(f"visitor-{i}" for i in range(500) if canary_bucket(f"visitor-{i}") < 10)
    stable_user = next(f"visitor-{i}" for i in range(500) if canary_bucket(f"visitor-{i}") >= 10)
    ask(world.client, question(), user=canary_user)
    ask(world.client, question(), user=stable_user)
    assert [r.model for r in world.owl.requests] == ["owl-large-v2", "owl-large"]


def run_traffic(world: World, users: int) -> None:
    for i in range(users):
        ask(world.client, question(), user=f"visitor-{i}")


def test_a_failing_canary_is_rolled_back(make_world) -> None:  # type: ignore[no-untyped-def]
    world = make_world(canary_percent=20.0)
    world.owl.fail_models = {"owl-large-v2"}
    world.parrot.outage = True
    run_traffic(world, 250)
    assert world.client.post("/internal/releases/evaluate").json()["verdict"] == "rollback"
    canary_user = next(f"visitor-{i}" for i in range(500) if canary_bucket(f"visitor-{i}") < 20)
    after = ask(world.client, question(), user=canary_user)
    assert after.status_code == 200
    assert after.headers["X-Release"] == "stable"


def test_a_healthy_canary_is_promoted(make_world) -> None:  # type: ignore[no-untyped-def]
    world = make_world(canary_percent=20.0)
    run_traffic(world, 250)
    assert world.client.post("/internal/releases/evaluate").json()["verdict"] == "promote"


def test_too_little_canary_traffic_means_wait(make_world) -> None:  # type: ignore[no-untyped-def]
    world = make_world(canary_percent=20.0)
    run_traffic(world, 40)
    assert world.client.post("/internal/releases/evaluate").json()["verdict"] == "wait"
