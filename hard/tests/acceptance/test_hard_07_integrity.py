"""Ticket 07: two families, one kitten."""

import random
import sqlite3
import threading

from zoo_platform.infrastructure.database import Database, sqlite_factory
from zp_testkit import World, auth


def etag_of(world: World, kitten: str = "pixel") -> str:
    response = world.client.get(f"/v1/kittens/{kitten}", headers=auth())
    assert "ETag" in response.headers, "kittens must carry an ETag"
    return response.headers["ETag"]


def adopt(client, family: str, etag: str | None, kitten: str = "pixel"):  # type: ignore[no-untyped-def]
    headers = auth()
    if etag is not None:
        headers["If-Match"] = etag
    return client.post(f"/v1/kittens/{kitten}/adoption", json={"family": family}, headers=headers)


def test_an_adoption_needs_if_match(world: World) -> None:
    etag_of(world)
    assert adopt(world.client, "the Martins", None).status_code == 428


def test_a_stale_etag_is_refused(world: World) -> None:
    etag = etag_of(world)
    first = adopt(world.client, "the Martins", etag)
    assert first.status_code == 200
    assert first.headers["ETag"] != etag
    assert adopt(world.client, "the Nguyens", etag).status_code == 412
    assert (
        world.client.get("/v1/kittens/pixel", headers=auth()).json()["adopted_by"] == "the Martins"
    )


def test_simultaneous_adoptions_have_one_winner(world: World) -> None:
    etag = etag_of(world)
    barrier = threading.Barrier(6)
    results: list[tuple[str, int]] = []

    def family(name: str) -> None:
        client = world.replica()
        barrier.wait()
        results.append((name, adopt(client, name, etag).status_code))

    threads = [threading.Thread(target=family, args=(f"family-{i}",)) for i in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    winners = [name for name, status in results if status == 200]
    assert len(winners) == 1
    assert sorted(status for _, status in results) == [200] + [412] * 5
    assert world.client.get("/v1/kittens/pixel", headers=auth()).json()["adopted_by"] == winners[0]


def pantry(world: World, pantry_id: str) -> int:
    return int(world.client.get(f"/v1/pantries/{pantry_id}", headers=auth()).json()["food_kg"])


def transfer(client, source: str, target: str, kg: int):  # type: ignore[no-untyped-def]
    return client.post(
        "/v1/pantries/transfers",
        json={"source": source, "target": target, "kg": kg},
        headers=auth(),
    )


def test_a_transfer_to_an_unknown_pantry_changes_nothing(world: World) -> None:
    assert transfer(world.client, "north", "atlantis", 10).status_code == 404
    assert pantry(world, "north") == 100


def test_an_overdraft_is_refused(world: World) -> None:
    assert transfer(world.client, "east", "north", 1).status_code == 409
    assert (pantry(world, "east"), pantry(world, "north")) == (0, 100)


def test_concurrent_transfers_conserve_food(world: World) -> None:
    assert pantry(world, "north") + pantry(world, "south") + pantry(world, "east") == 200
    barrier = threading.Barrier(8)
    statuses: list[int] = []

    def keeper(seed: int) -> None:
        client = world.replica()
        rng = random.Random(seed)
        barrier.wait()
        for _ in range(8):
            source, target = rng.sample(["north", "south", "east"], 2)
            statuses.append(transfer(client, source, target, rng.randint(1, 15)).status_code)

    threads = [threading.Thread(target=keeper, args=(n,)) for n in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert set(statuses) <= {200, 409}
    stock = [pantry(world, name) for name in ("north", "south", "east")]
    assert sum(stock) == 200, stock
    assert min(stock) >= 0


def test_kittens_get_a_slug_backfilled_in_batches(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = str(tmp_path / "legacy.db")
    Database(sqlite_factory(path)).migrate(target="0001")
    conn = sqlite3.connect(path)
    conn.executemany(
        "INSERT INTO kittens (id, tenant, name) VALUES (?, 'paris', ?)",
        [(f"k{i}", f"Little Kitten {i}") for i in range(1_300)],
    )
    conn.commit()
    conn.close()

    statements: list[str] = []

    def traced() -> sqlite3.Connection:
        connection = sqlite_factory(path)()
        connection.set_trace_callback(statements.append)
        return connection

    Database(traced).migrate()
    updates = [s for s in statements if s.lstrip().upper().startswith("UPDATE") and "kittens" in s]
    assert len(updates) >= 3, "backfill 1300 rows in batches of at most 500"
    check = sqlite3.connect(path)
    slugs = dict(check.execute("SELECT id, slug FROM kittens").fetchall())
    check.close()
    assert slugs["k7"] == "little-kitten-7"
    assert None not in slugs.values()


def test_new_kittens_get_a_slug(world: World) -> None:
    world.client.post("/v1/kittens", json={"id": "tofu", "name": "Tofu The Brave"}, headers=auth())
    assert world.client.get("/v1/kittens/tofu", headers=auth()).json()["slug"] == "tofu-the-brave"
