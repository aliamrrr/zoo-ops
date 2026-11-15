"""Ticket 01: the Owl bill."""

from zp_testkit import World, ask, auth

QUESTION = "Why do otters hold hands?"


def test_a_repeated_question_reaches_the_model_once(world: World) -> None:
    first = ask(world.client, QUESTION)
    second = ask(world.client, QUESTION, user="visitor-2")
    assert first.status_code == second.status_code == 200
    assert first.json()["answer"] == second.json()["answer"]
    assert len(world.owl.requests) == 1


def test_wording_differences_do_not_matter(world: World) -> None:
    ask(world.client, "Why do otters hold hands?")
    ask(world.client, "   why do OTTERS hold hands?  ")
    assert len(world.owl.requests) == 1


def test_sampled_answers_are_not_cached(world: World) -> None:
    ask(world.client, QUESTION, temperature=0.8)
    ask(world.client, QUESTION, temperature=0.8)
    assert len(world.owl.requests) == 2


def test_every_replica_shares_the_cache(world: World) -> None:
    ask(world.client, QUESTION)
    ask(world.replica(), QUESTION)
    assert len(world.owl.requests) == 1


def test_cached_entries_expire_within_ten_minutes(world: World) -> None:
    ask(world.client, QUESTION)
    keys = world.redis.keys("*")
    assert keys, "nothing was stored in Redis"
    assert all(0 < world.redis.ttl(key) <= 600 for key in keys)


def test_a_fact_update_reaches_visitors_at_once(world: World) -> None:
    ask(world.client, "How long do lions sleep?")
    updated = world.client.put(
        "/v1/owl/facts/lion", json={"text": "Lions now nap on a schedule."}, headers=auth()
    )
    assert updated.status_code == 204
    answer = ask(world.client, "How long do lions sleep?").json()["answer"]
    assert "Lions now nap on a schedule." in answer


def test_failures_are_not_cached(world: World) -> None:
    world.owl.outage = world.parrot.outage = True
    assert ask(world.client, QUESTION).status_code >= 500
    world.owl.outage = world.parrot.outage = False
    calls = len(world.owl.requests)
    assert ask(world.client, QUESTION).status_code == 200
    assert len(world.owl.requests) > calls
