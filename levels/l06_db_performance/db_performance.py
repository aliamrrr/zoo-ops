"""Level 06: indexes, EXPLAIN, N+1 queries, cursor pagination and connection pooling.

SQLite stands in for Postgres here: the ideas are identical, only the EXPLAIN output differs.
"""

from __future__ import annotations

import base64
import json
import queue
import random
import sqlite3
import threading
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

C = TypeVar("C")

SCHEMA = """
CREATE TABLE enclosures (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE animals (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    species TEXT NOT NULL,
    enclosure_id INTEGER NOT NULL REFERENCES enclosures (id),
    arrived_at INTEGER NOT NULL
);
"""

SPECIES = ("cat", "fox", "owl", "mole", "otter", "goose", "canary", "beaver")

# The catalog query catalog_page() must serve, here with a cursor already decoded:
CATALOG_QUERY_SHAPE = (
    "SELECT id, name, arrived_at FROM animals "
    "WHERE species = ? AND (arrived_at, id) < (?, ?) "
    "ORDER BY arrived_at DESC, id DESC LIMIT ?"
)


def index_statements() -> list[str]:
    """CREATE INDEX statement(s) so that CATALOG_QUERY_SHAPE neither scans the whole table
    nor sorts in a temporary B-tree. Check your answer with explain()."""
    # TODO(level 06): return a list of SQL strings.
    raise NotImplementedError("index_statements")


def connect(path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    for statement in index_statements():
        conn.execute(statement)


def seed(conn: sqlite3.Connection, animals: int = 2_000, seed_value: int = 6) -> None:
    rng = random.Random(seed_value)
    conn.executemany(
        "INSERT INTO enclosures (id, name) VALUES (?, ?)",
        [(i, f"Enclosure {i}") for i in range(1, 41)],
    )
    conn.executemany(
        "INSERT INTO animals (name, species, enclosure_id, arrived_at) VALUES (?, ?, ?, ?)",
        [
            (
                f"{rng.choice(SPECIES)}-{i}",
                rng.choice(SPECIES),
                rng.randint(1, 40),
                rng.randint(1_000, 1_500),
            )
            for i in range(animals)
        ],
    )
    conn.commit()


def explain(conn: sqlite3.Connection, sql: str, params: Sequence[Any]) -> list[str]:
    """The `detail` column of EXPLAIN QUERY PLAN, e.g. 'SCAN animals' or
    'SEARCH animals USING INDEX ...'. 'USE TEMP B-TREE FOR ORDER BY' means an extra sort."""
    return [row["detail"] for row in conn.execute(f"EXPLAIN QUERY PLAN {sql}", params)]


@dataclass(frozen=True)
class Page:
    items: list[dict[str, Any]]
    next_cursor: str | None


def encode_cursor(arrived_at: int, animal_id: int) -> str:
    raw = json.dumps([arrived_at, animal_id]).encode()
    return base64.urlsafe_b64encode(raw).decode()


def decode_cursor(cursor: str) -> tuple[int, int]:
    arrived_at, animal_id = json.loads(base64.urlsafe_b64decode(cursor.encode()))
    return int(arrived_at), int(animal_id)


def catalog_page(
    conn: sqlite3.Connection, species: str, limit: int, cursor: str | None = None
) -> Page:
    """One page of a species, newest arrivals first (arrived_at DESC, id DESC).

    Contract:
    - items are dicts with the keys id, name, arrived_at
    - keyset pagination: the cursor holds (arrived_at, id) of the last row already served and
      the next page starts strictly after it (see CATALOG_QUERY_SHAPE). Never use OFFSET: an
      animal arriving between two page loads would shift every row and duplicate one
    - next_cursor is None when there is nothing after this page
      (tip: fetch limit + 1 rows to know)
    """
    # TODO(level 06)
    raise NotImplementedError("catalog_page")


def animals_with_enclosure(
    conn: sqlite3.Connection, animal_ids: Sequence[int]
) -> list[dict[str, Any]]:
    """[{"id", "name", "enclosure"}] in the order of `animal_ids`.

    This works but runs 1 + N queries: one for the animals, then one per animal for its
    enclosure. With 50 animals that is 51 round trips to the database.
    TODO(level 06): make it a single query (a JOIN with WHERE id IN (...)).
    """
    if not animal_ids:
        return []
    placeholders = ",".join("?" for _ in animal_ids)
    animals = conn.execute(
        f"SELECT id, name, enclosure_id FROM animals WHERE id IN ({placeholders})",
        list(animal_ids),
    ).fetchall()
    by_id = {}
    for animal in animals:
        enclosure = conn.execute(
            "SELECT name FROM enclosures WHERE id = ?", (animal["enclosure_id"],)
        ).fetchone()
        by_id[animal["id"]] = {
            "id": animal["id"],
            "name": animal["name"],
            "enclosure": enclosure["name"],
        }
    return [by_id[i] for i in animal_ids if i in by_id]


class PoolExhausted(Exception):
    pass


class ConnectionPool(Generic[C]):
    """Opening a database connection costs a TCP handshake, TLS and auth: reuse them.
    In production this is SQLAlchemy's pool, psycopg_pool or PgBouncer."""

    def __init__(self, factory: Callable[[], C], size: int, timeout: float) -> None:
        self._factory = factory
        self._size = size
        self._timeout = timeout
        self._idle: queue.LifoQueue[C] = queue.LifoQueue()
        self._lock = threading.Lock()
        self.created = 0

    @contextmanager
    def connection(self) -> Iterator[C]:
        """Borrow a connection for the block and always give it back, even on error.

        Contract:
        - reuse an idle connection first
        - otherwise open a new one with the factory, only while fewer than `size` exist
          (protect `created` with the lock: several threads borrow at once)
        - otherwise wait up to `timeout` seconds for one to come back, then raise PoolExhausted
        """
        # TODO(level 06)
        raise NotImplementedError("ConnectionPool.connection")
