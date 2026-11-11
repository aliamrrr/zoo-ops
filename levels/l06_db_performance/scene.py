"""Scene 06: Digby browses the cat catalog while new cats keep arriving."""

from __future__ import annotations

import sqlite3
import threading
import time

from levels.l06_db_performance.db_performance import (
    CATALOG_QUERY_SHAPE,
    SCHEMA,
    ConnectionPool,
    animals_with_enclosure,
    catalog_page,
    connect,
    explain,
    index_statements,
    seed,
)
from zoo.kit import Scene


def count_selects(conn: sqlite3.Connection) -> list[str]:
    statements: list[str] = []
    conn.set_trace_callback(statements.append)
    return statements


def play(scene: Scene) -> None:
    conn = connect()
    conn.executescript(SCHEMA)
    seed(conn, animals=3_000)

    plan_before = " | ".join(explain(conn, CATALOG_QUERY_SHAPE, ("cat", 1_400, 99, 25)))
    for statement in index_statements():
        conn.execute(statement)
    plan = " | ".join(explain(conn, CATALOG_QUERY_SHAPE, ("cat", 1_400, 99, 25)))
    scene.info(f"Plan without index: {plan_before}")
    scene.metric("query plan", plan)
    scene.check(
        "SCAN animals" not in plan and "TEMP B-TREE" not in plan,
        "The catalog query walks an index in order: no full scan, no sort.",
        f"The catalog query still scans or sorts: {plan}",
    )

    cats_at_start = [
        row["id"]
        for row in conn.execute(
            "SELECT id FROM animals WHERE species = 'cat' ORDER BY arrived_at DESC, id DESC"
        )
    ]
    served: list[int] = []
    cursor = None
    arrivals = 0
    while True:
        page = catalog_page(conn, "cat", 25, cursor)
        served.extend(item["id"] for item in page.items)
        conn.execute(
            "INSERT INTO animals (name, species, enclosure_id, arrived_at) "
            "VALUES (?, 'cat', 1, ?)",
            (f"kitten-{arrivals}", 10_000 + arrivals),
        )
        arrivals += 1
        if page.next_cursor is None or arrivals > 500:
            break
        cursor = page.next_cursor
    duplicates = len(served) - len(set(served))
    scene.info(f"Digby reads {arrivals} pages while {arrivals} new kittens arrive.")
    scene.metric("duplicates served", duplicates)
    scene.check(
        duplicates == 0 and served == cats_at_start,
        f"All {len(cats_at_start)} cats listed exactly once, in order, despite the arrivals.",
        f"The catalog served {duplicates} duplicates and "
        f"{len(set(cats_at_start) - set(served))} cats went missing.",
    )

    statements = count_selects(conn)
    animals_with_enclosure(conn, list(range(1, 51)))
    conn.set_trace_callback(None)
    tunnels = sum(1 for s in statements if s.lstrip().upper().startswith("SELECT"))
    scene.metric("tunnels for 50 animals", tunnels)
    scene.check(
        tunnels == 1,
        "The enclosure report needs a single tunnel (one JOIN).",
        f"Digby dug {tunnels} tunnels for 50 animals: the N+1 query strikes.",
    )

    pool: ConnectionPool[object] = ConnectionPool(object, size=4, timeout=2.0)
    with pool.connection():
        pass
    done: list[int] = []

    def visitor(n: int) -> None:
        with pool.connection():
            time.sleep(0.005)
            done.append(n)

    threads = [threading.Thread(target=visitor, args=(n,)) for n in range(40)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    scene.metric("connections opened", pool.created)
    scene.check(
        len(done) == 40 and pool.created <= 4,
        f"40 concurrent visitors were served by {pool.created} of 4 pooled connections.",
        f"{pool.created} connections opened for {len(done)} visitors. The pool leaks.",
    )
