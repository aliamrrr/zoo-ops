"""Ticket 03: the storm on the bridge."""

import itertools

from zp_testkit import World, ask

_counter = itertools.count()


def question() -> str:
    return f"Tell me about otters, take {next(_counter)}"


def test_every_model_call_has_a_deadline(world: World) -> None:
    ask(world.client, question())
    assert world.owl.requests
    assert all(r.timeout_s is not None and 0 < r.timeout_s <= 3 for r in world.owl.requests)


def test_transient_failures_are_retried_with_backoff(world: World) -> None:
    world.owl.failures_left = 2
    response = ask(world.client, question())
    assert response.status_code == 200
    assert response.json()["model"] == "owl-large"
    assert len(world.owl.requests) == 3
    first, second = world.clock.sleeps[:2]
    assert 0 <= first <= 0.2
    assert 0 <= second <= 0.4


def test_an_outage_falls_back_to_the_parrot(world: World) -> None:
    world.owl.outage = True
    response = ask(world.client, question())
    assert response.status_code == 200
    assert response.json()["model"] == "parrot-small"
    assert len(world.owl.requests) == 3
    assert len(world.parrot.requests) == 1


def test_the_breaker_stops_calling_a_dead_owl(world: World) -> None:
    world.owl.outage = True
    for _ in range(3):
        ask(world.client, question())
    calls = len(world.owl.requests)
    for _ in range(5):
        assert ask(world.client, question()).json()["model"] == "parrot-small"
    assert len(world.owl.requests) == calls


def test_the_breaker_tries_again_after_thirty_seconds(world: World) -> None:
    world.owl.outage = True
    for _ in range(3):
        ask(world.client, question())
    world.owl.outage = False
    world.clock.advance(10)
    assert ask(world.client, question()).json()["model"] == "parrot-small"
    world.clock.advance(20)
    assert ask(world.client, question()).json()["model"] == "owl-large"
    assert ask(world.client, question()).json()["model"] == "owl-large"


def test_rejected_prompts_are_not_retried(world: World) -> None:
    world.owl.reject = True
    response = ask(world.client, question())
    assert response.status_code == 422
    assert len(world.owl.requests) == 1
    assert world.parrot.requests == []
    assert world.clock.sleeps == []
