"""Ticket 02: the pigeon flood."""

from zp_testkit import World, ask


def flood(client, user: str, count: int, start: int = 0) -> list[int]:  # type: ignore[no-untyped-def]
    return [
        ask(client, f"question {start + i} about otters", user=user).status_code
        for i in range(count)
    ]


def test_sixty_requests_a_minute_per_caller(world: World) -> None:
    statuses = flood(world.client, "pigeon", 61)
    assert statuses[:60] == [200] * 60
    assert statuses[60] == 429


def test_a_rejection_says_when_to_come_back(world: World) -> None:
    flood(world.client, "pigeon", 60)
    rejected = ask(world.client, "one more about otters", user="pigeon")
    assert rejected.status_code == 429
    assert rejected.headers["Retry-After"] == "1"
    assert rejected.json()["limit"] == "requests"


def test_the_budget_refills_over_time(world: World) -> None:
    flood(world.client, "pigeon", 60)
    world.clock.advance(2)
    assert flood(world.client, "pigeon", 3, start=100) == [200, 200, 429]


def test_callers_have_separate_budgets(world: World) -> None:
    flood(world.client, "pigeon", 61)
    assert ask(world.client, "where are the worms?", user="hedgehog").status_code == 200


def test_huge_prompts_hit_the_token_budget_and_cost_nothing(world: World) -> None:
    huge = ask(world.client, "otters " * 3_430, user="python")
    assert huge.status_code == 429
    assert huge.json()["limit"] == "tokens"
    assert flood(world.client, "python", 60) == [200] * 60


def test_replicas_share_one_budget(world: World) -> None:
    other = world.replica()
    assert flood(world.client, "pigeon", 30) == [200] * 30
    assert flood(other, "pigeon", 30, start=30) == [200] * 30
    assert ask(other, "the last straw about otters", user="pigeon").status_code == 429


def test_every_redis_key_expires(world: World) -> None:
    flood(world.client, "pigeon", 5)
    keys = world.redis.keys("*")
    assert keys, "nothing was stored in Redis"
    assert all(0 < world.redis.ttl(key) <= 600 for key in keys)
