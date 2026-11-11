"""Scene 04: Miso orders three meals over a network that loses most responses."""

from __future__ import annotations

from levels.l04_idempotency.idempotency import (
    IdempotencyConflict,
    IdempotencyStore,
    StoredResponse,
    belly,
    connect,
    record_meal,
)
from zoo.kit import Scene

MEALS = [("order-101", 50), ("order-102", 50), ("order-103", 50)]
TRIES_PER_MEAL = 3


def play(scene: Scene) -> None:
    conn = connect()
    store = IdempotencyStore(conn)
    expected = sum(grams for _, grams in MEALS)

    for order_id, grams in MEALS:
        payload = {"cat": "miso", "grams": grams, "order_id": order_id}

        def serve(order_id: str = order_id, grams: int = grams) -> StoredResponse:
            record_meal(conn, order_id, "miso", grams)
            return StoredResponse(201, {"served": grams})

        for attempt in range(1, TRIES_PER_MEAL + 1):
            response = store.execute(f"idem-{order_id}", payload, serve)
            if attempt < TRIES_PER_MEAL:
                continue
            if response.replayed:
                scene.info(f"{order_id}: response lost twice, the third retry gets a replay.")

    scene.info(
        f"Miso orders {len(MEALS)} meals of 50 g, every request is sent "
        f"{TRIES_PER_MEAL} times because responses get lost."
    )
    eaten = belly(conn, "miso")
    scene.metric("grams eaten", eaten)
    scene.metric("grams ordered", expected)
    scene.check(
        eaten == expected,
        f"Miso ate exactly {expected} g. Retries replayed the stored response.",
        f"Miso ate {eaten} g instead of {expected} g. He now rolls instead of walking.",
    )

    for order_id, grams in MEALS:
        record_meal(conn, order_id, "miso", grams)
    eaten_after_batch = belly(conn, "miso")
    scene.check(
        eaten_after_batch == expected,
        "A nightly batch replayed the orders directly in the DB: UNIQUE order_id kept it safe.",
        f"A batch job replayed the orders and Miso's belly jumped to {eaten_after_batch} g.",
    )

    try:
        store.execute(
            "idem-order-101",
            {"cat": "miso", "grams": 5000, "order_id": "order-101"},
            lambda: StoredResponse(201, {"served": 5000}),
        )
    except IdempotencyConflict:
        scene.good("A buggy client reused a key for a 5 kg order: rejected with 422.")
    else:
        scene.bad("A reused key with a different 5 kg payload was accepted silently.")
