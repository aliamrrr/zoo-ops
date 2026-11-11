"""Level 04: idempotency keys, UNIQUE constraints and upserts.

A client that times out cannot know whether the server did the work. It retries with the
same Idempotency-Key header, and the server must answer with the first result instead of
doing the work again. Two lines of defense:
    1. the API layer: an idempotency_keys table remembers each key and its response
    2. the database: a UNIQUE business key (order_id) plus upserts, for every other writer
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS idempotency_keys (
    key TEXT PRIMARY KEY,
    request_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('in_progress', 'completed')),
    response TEXT
);
CREATE TABLE IF NOT EXISTS meals (
    order_id TEXT PRIMARY KEY,
    cat TEXT NOT NULL,
    grams INTEGER NOT NULL CHECK (grams > 0)
);
CREATE TABLE IF NOT EXISTS bellies (
    cat TEXT PRIMARY KEY,
    grams_eaten INTEGER NOT NULL
);
"""


def connect(path: str = ":memory:") -> sqlite3.Connection:
    """Autocommit connection: transactions are opened explicitly with `transaction()`."""
    conn = sqlite3.connect(path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    conn.execute("COMMIT")


@dataclass(frozen=True)
class StoredResponse:
    status_code: int
    body: dict[str, Any]
    replayed: bool = False


class IdempotencyConflict(Exception):
    """The key was already used with a different payload (HTTP 422)."""


class RequestInProgress(Exception):
    """The first request with this key is still running (HTTP 409)."""


def fingerprint(payload: Mapping[str, Any]) -> str:
    """sha256 hex digest of the canonical JSON of the payload (sort_keys, compact separators),
    so {"a": 1, "b": 2} and {"b": 2, "a": 1} share a fingerprint."""
    # TODO(level 04)
    raise NotImplementedError("fingerprint")


class IdempotencyStore:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def execute(
        self,
        key: str,
        payload: Mapping[str, Any],
        handler: Callable[[], StoredResponse],
    ) -> StoredResponse:
        """Run `handler` at most once per idempotency key.

        Contract:
        1. claim the key: INSERT (key, fingerprint, 'in_progress') ... ON CONFLICT(key) DO NOTHING,
           then read cursor.rowcount: 1 means this call owns the key
        2. key already there:
           - different fingerprint      -> raise IdempotencyConflict
           - status still 'in_progress' -> raise RequestInProgress
           - status 'completed'         -> return the stored response with replayed=True
        3. owner: run the handler, store {"status_code", "body"} as JSON in `response`,
           set status to 'completed', return the handler's response
        4. handler raised: DELETE the claim so a later retry can run, then re-raise
        """
        # TODO(level 04)
        raise NotImplementedError("IdempotencyStore.execute")


def record_meal(conn: sqlite3.Connection, order_id: str, cat: str, grams: int) -> bool:
    """Store a meal at most once per order_id and add it to the cat's belly.

    Contract:
    - one transaction for both writes (use `transaction(conn)`)
    - INSERT INTO meals ... ON CONFLICT(order_id) DO NOTHING, rowcount tells if it is new
    - only a new meal updates bellies, with an upsert:
      INSERT ... ON CONFLICT(cat) DO UPDATE SET grams_eaten = grams_eaten + excluded.grams_eaten
    - return True when the meal was new, False for a duplicate
    """
    # TODO(level 04)
    raise NotImplementedError("record_meal")


def belly(conn: sqlite3.Connection, cat: str) -> int:
    row = conn.execute("SELECT grams_eaten FROM bellies WHERE cat = ?", (cat,)).fetchone()
    return 0 if row is None else int(row["grams_eaten"])


def to_json(response: StoredResponse) -> str:
    return json.dumps({"status_code": response.status_code, "body": response.body})
