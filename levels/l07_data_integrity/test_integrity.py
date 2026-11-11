import random
import sqlite3
import threading
from pathlib import Path

import pytest

from levels.l07_data_integrity.integrity import (
    AdoptionConflict,
    InsufficientFood,
    UnknownPantry,
    adopt,
    backfill_in_batches,
    connect,
    expand_schema,
    read_kitten,
    transfer_food,
)


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "zoo.db")
    conn = connect(path)
    conn.executemany(
        "INSERT INTO pantries (id, food_kg) VALUES (?, ?)",
        [("north", 100), ("south", 100), ("east", 0)],
    )
    conn.executemany(
        "INSERT INTO kittens (id, name) VALUES (?, ?)", [(f"k{i}", f"Kitten{i}") for i in range(25)]
    )
    conn.close()
    return path


def stock(conn: sqlite3.Connection) -> dict[str, int]:
    return {row["id"]: row["food_kg"] for row in conn.execute("SELECT * FROM pantries")}


def test_transfer_moves_food(db_path: str) -> None:
    conn = connect(db_path)
    transfer_food(conn, "north", "east", 30)
    assert stock(conn) == {"north": 70, "south": 100, "east": 30}


def test_transfer_refuses_overdraft(db_path: str) -> None:
    conn = connect(db_path)
    with pytest.raises(InsufficientFood):
        transfer_food(conn, "east", "north", 1)
    assert stock(conn) == {"north": 100, "south": 100, "east": 0}


def test_transfer_to_unknown_pantry_rolls_back(db_path: str) -> None:
    conn = connect(db_path)
    with pytest.raises(UnknownPantry):
        transfer_food(conn, "north", "atlantis", 10)
    assert stock(conn)["north"] == 100, "the debit must be rolled back"
    assert not conn.in_transaction, "the transaction must be closed after an error"


def test_transfer_from_unknown_pantry(db_path: str) -> None:
    with pytest.raises(UnknownPantry):
        transfer_food(connect(db_path), "atlantis", "north", 10)


def test_concurrent_transfers_conserve_food(db_path: str) -> None:
    barrier = threading.Barrier(8)
    errors: list[BaseException] = []

    def keeper(seed: int) -> None:
        conn = connect(db_path)
        rng = random.Random(seed)
        barrier.wait()
        for _ in range(25):
            source, target = rng.sample(["north", "south", "east"], 2)
            try:
                transfer_food(conn, source, target, rng.randint(1, 15))
            except InsufficientFood:
                pass
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

    threads = [threading.Thread(target=keeper, args=(n,)) for n in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    final = stock(connect(db_path))
    assert sum(final.values()) == 200, f"food was created or lost: {final}"
    assert min(final.values()) >= 0


def test_adopt_bumps_the_version(db_path: str) -> None:
    conn = connect(db_path)
    assert adopt(conn, "k1", "the Martins", expected_version=0) == 1
    kitten = read_kitten(conn, "k1")
    assert kitten["adopted_by"] == "the Martins" and kitten["version"] == 1


def test_adopt_with_stale_version_fails(db_path: str) -> None:
    conn = connect(db_path)
    adopt(conn, "k1", "the Martins", expected_version=0)
    with pytest.raises(AdoptionConflict):
        adopt(conn, "k1", "the Nguyens", expected_version=0)


def test_adopt_an_adopted_kitten_fails(db_path: str) -> None:
    conn = connect(db_path)
    adopt(conn, "k1", "the Martins", expected_version=0)
    with pytest.raises(AdoptionConflict):
        adopt(conn, "k1", "the Nguyens", expected_version=1)
    assert read_kitten(conn, "k1")["adopted_by"] == "the Martins"


def test_simultaneous_adoptions_have_one_winner(db_path: str) -> None:
    barrier = threading.Barrier(6)
    winners: list[str] = []

    def family(name: str) -> None:
        conn = connect(db_path)
        version = read_kitten(conn, "k2")["version"]
        barrier.wait()
        try:
            adopt(conn, "k2", name, version)
            winners.append(name)
        except AdoptionConflict:
            pass

    threads = [threading.Thread(target=family, args=(f"family-{n}",)) for n in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(winners) == 1
    assert read_kitten(connect(db_path), "k2")["adopted_by"] == winners[0]


def test_backfill_runs_in_batches(db_path: str) -> None:
    conn = connect(db_path)
    expand_schema(conn)
    updates: list[str] = []
    conn.set_trace_callback(lambda sql: updates.append(sql) if sql.startswith("UPDATE") else None)
    assert backfill_in_batches(conn, batch_size=10) == 3
    slugs = [row["slug"] for row in conn.execute("SELECT slug FROM kittens ORDER BY id")]
    assert None not in slugs and "kitten0" in slugs
    assert len(updates) <= 4, "25 rows by 10 is 3 batches plus at most one empty check"


def test_backfill_is_resumable(db_path: str) -> None:
    conn = connect(db_path)
    expand_schema(conn)
    backfill_in_batches(conn, batch_size=100)
    assert backfill_in_batches(conn, batch_size=100) == 0


def test_backfill_keeps_old_code_working(db_path: str) -> None:
    conn = connect(db_path)
    expand_schema(conn)
    conn.execute("INSERT INTO kittens (id, name) VALUES ('legacy', 'Written by old code')")
    backfill_in_batches(conn, batch_size=7)
    assert read_kitten(conn, "legacy")["slug"] == "written by old code"
