"""Ticket 04: the double meals."""

import threading

from zp_testkit import World, auth

ANIMAL = 3


def order(client, key: str | None = None, grams: int = 50, user: str = "keeper-1"):  # type: ignore[no-untyped-def]
    headers = auth(user)
    if key is not None:
        headers["Idempotency-Key"] = key
    return client.post(
        "/v1/kitchen/orders", json={"animal_id": ANIMAL, "grams": grams}, headers=headers
    )


def belly(world: World) -> int:
    return int(world.client.get(f"/v1/animals/{ANIMAL}/belly", headers=auth()).json()["grams"])


def test_retries_with_the_same_key_feed_once(world: World) -> None:
    before = belly(world)
    responses = [order(world.client, key="order-7f3a") for _ in range(3)]
    assert [r.status_code for r in responses] == [201, 201, 201]
    assert len({r.json()["order_id"] for r in responses}) == 1
    assert "Idempotent-Replayed" not in responses[0].headers
    assert responses[1].headers["Idempotent-Replayed"] == "true"
    assert belly(world) == before + 50


def test_a_key_reused_for_another_order_is_refused(world: World) -> None:
    before = belly(world)
    order(world.client, key="order-1", grams=50)
    assert order(world.client, key="order-1", grams=500).status_code == 422
    assert belly(world) == before + 50


def test_concurrent_retries_feed_once(world: World) -> None:
    before = belly(world)
    barrier = threading.Barrier(8)
    statuses: list[int] = []

    def retry() -> None:
        client = world.replica()
        barrier.wait()
        statuses.append(order(client, key="order-storm").status_code)

    threads = [threading.Thread(target=retry) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert set(statuses) <= {201, 409}
    assert 201 in statuses
    assert belly(world) == before + 50


def test_keys_belong_to_their_caller(world: World) -> None:
    before = belly(world)
    order(world.client, key="shared-key", user="keeper-1")
    order(world.client, key="shared-key", user="keeper-2")
    assert belly(world) == before + 100


def test_supplier_deliveries_are_counted_once(world: World) -> None:
    before = belly(world)
    deliveries = [
        {"reference": "inv-1", "animal_id": ANIMAL, "grams": 40},
        {"reference": "inv-2", "animal_id": ANIMAL, "grams": 30},
    ]
    first = world.client.post(
        "/v1/kitchen/supplier-deliveries", json={"deliveries": deliveries}, headers=auth("supplier")
    )
    again = world.client.post(
        "/v1/kitchen/supplier-deliveries",
        json={
            "deliveries": [*deliveries, {"reference": "inv-3", "animal_id": ANIMAL, "grams": 20}]
        },
        headers=auth("supplier"),
    )
    assert first.json()["accepted"] == 2
    assert again.json()["accepted"] == 1
    assert belly(world) == before + 90
