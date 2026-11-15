"""Ticket 06: the slow visitor guide."""

import sqlite3
import threading

from zp_testkit import World, auth


def browse(client, cursor: str | None = None, limit: int = 20, species: str = "cat"):  # type: ignore[no-untyped-def]
    params: dict[str, object] = {"species": species, "limit": limit}
    if cursor:
        params["cursor"] = cursor
    return client.get("/v1/animals", params=params, headers=auth())


def expected(world: World, species: str = "cat") -> list[int]:
    rows = world.sql(
        "SELECT id FROM animals WHERE species = ? AND tenant = 'paris' "
        "ORDER BY arrived_at DESC, id DESC",
        (species,),
    )
    return [row["id"] for row in rows]


def test_pages_follow_an_opaque_cursor(world: World) -> None:
    seen: list[int] = []
    cursor = None
    for _ in range(50):
        body = browse(world.client, cursor, limit=15, species="fox").json()
        seen.extend(item["id"] for item in body["items"])
        cursor = body.get("next_cursor")
        if cursor is None:
            break
    assert seen == expected(world, "fox")


def test_new_arrivals_do_not_shift_the_next_page(world: World) -> None:
    before = expected(world)
    first = browse(world.client).json()
    for i in range(5):
        world.client.post(
            "/v1/animals",
            json={"name": f"kitten-{i}", "species": "cat", "enclosure_id": 1},
            headers=auth(),
        )
    world.clock.advance(1)
    second = browse(world.client, first["next_cursor"]).json()
    ids = [item["id"] for item in first["items"] + second["items"]]
    assert ids == before[:40]


def test_a_page_costs_at_most_two_queries(world: World) -> None:
    browse(world.client)
    world.statements.clear()
    assert browse(world.client).status_code == 200
    selects = [s for s in world.statements if s.lstrip().upper().startswith(("SELECT", "WITH"))]
    assert len(selects) <= 2, selects


def test_the_catalog_query_uses_an_index(world: World) -> None:
    world.statements.clear()
    browse(world.client)
    catalog = [
        s
        for s in world.statements
        if "animals" in s and "species" in s and s.lstrip().upper().startswith("SELECT")
    ]
    assert catalog
    conn = sqlite3.connect(world.db_path)
    try:
        details = [row[3] for row in conn.execute(f"EXPLAIN QUERY PLAN {catalog[0]}")]
    finally:
        conn.close()
    assert not any(detail.startswith("SCAN") for detail in details), details
    assert not any("TEMP B-TREE" in detail for detail in details), details


def test_connections_are_pooled(world: World) -> None:
    client = world.client
    baseline = world.connections_opened
    for _ in range(20):
        browse(client)
    errors: list[int] = []

    def visitor() -> None:
        status = browse(client).status_code
        if status != 200:
            errors.append(status)

    threads = [threading.Thread(target=visitor) for _ in range(12)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    assert world.connections_opened - baseline <= 4
