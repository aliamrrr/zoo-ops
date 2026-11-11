"""Scene 07: a busy adoption day at the dam."""

from __future__ import annotations

import random
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path

from levels.l07_data_integrity.integrity import (
    AdoptionConflict,
    InsufficientFood,
    adopt,
    backfill_in_batches,
    connect,
    expand_schema,
    read_kitten,
    transfer_food,
)
from zoo.kit import Scene

PANTRIES = {"north": 120, "south": 80, "river": 0}


def run_threads(count: int, target: Callable[[int], None]) -> None:
    threads = [threading.Thread(target=target, args=(n,)) for n in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


def play(scene: Scene) -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
        path = str(Path(folder) / "dam.db")
        conn = connect(path)
        conn.executemany("INSERT INTO pantries (id, food_kg) VALUES (?, ?)", PANTRIES.items())
        conn.executemany(
            "INSERT INTO kittens (id, name) VALUES (?, ?)",
            [(f"k{i}", f"Kitten {i}") for i in range(200)],
        )
        conn.execute("INSERT INTO kittens (id, name) VALUES ('pixel', 'Pixel')")

        errors: list[Exception] = []

        def keeper(seed: int) -> None:
            local = connect(path)
            rng = random.Random(seed)
            for _ in range(20):
                source, target = rng.sample(list(PANTRIES), 2)
                try:
                    transfer_food(local, source, target, rng.randint(1, 20))
                except InsufficientFood:
                    pass
                except Exception as exc:  # noqa: BLE001 - re-raised in the main thread
                    errors.append(exc)
                    break
            local.close()

        run_threads(6, keeper)
        if errors:
            raise errors[0]
        rows = {row["id"]: row["food_kg"] for row in conn.execute("SELECT * FROM pantries")}
        total, expected = sum(rows.values()), sum(PANTRIES.values())
        scene.info("6 keepers move food between pantries at the same time, 120 transfers.")
        scene.metric("food in stock", f"{total} kg (expected {expected})")
        scene.check(
            total == expected and min(rows.values()) >= 0,
            "Not a single kilo was created or lost.",
            f"The pantries hold {total} kg instead of {expected} kg: lost updates.",
        )

        winners: list[str] = []
        barrier = threading.Barrier(2)

        def family(n: int) -> None:
            local = connect(path)
            version = read_kitten(local, "pixel")["version"]
            barrier.wait()
            try:
                adopt(local, "pixel", ["the Martins", "the Nguyens"][n], version)
                winners.append(["the Martins", "the Nguyens"][n])
            except AdoptionConflict:
                pass
            except Exception as exc:  # noqa: BLE001 - re-raised in the main thread
                errors.append(exc)
            local.close()

        run_threads(2, family)
        if errors:
            raise errors[0]
        scene.info("Two families click 'adopt Pixel' in the same millisecond.")
        scene.check(
            len(winners) == 1,
            f"Pixel goes home with {winners[0] if winners else '?'}, the other family gets a 409.",
            f"{len(winners)} families think they adopted Pixel. Somebody will cry.",
        )

        expand_schema(conn)
        batches = backfill_in_batches(conn, batch_size=50)
        empty = conn.execute("SELECT COUNT(*) FROM kittens WHERE slug IS NULL").fetchone()[0]
        scene.metric("migration batches", batches)
        scene.check(
            empty == 0 and batches >= 4,
            f"The slug column was backfilled in {batches} small batches, the dam never closed.",
            f"Backfill left {empty} rows empty or ran in {batches} giant batch(es).",
        )
        conn.close()
