"""Level 07: transactions, locks, race conditions and zero-downtime migrations.

Two requests running at the same time read the same row, both decide, both write: one write
is lost. The cures are atomic statements, transactions that take the write lock up front,
and optimistic locking with a version column. Schema changes follow expand and contract so
old and new code both keep working during a deploy.
"""

from __future__ import annotations

import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS pantries (
    id TEXT PRIMARY KEY,
    food_kg INTEGER NOT NULL CHECK (food_kg >= 0)
);
CREATE TABLE IF NOT EXISTS kittens (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    adopted_by TEXT,
    version INTEGER NOT NULL DEFAULT 0
);
"""


class InsufficientFood(Exception):
    pass


class UnknownPantry(LookupError):
    pass


class AdoptionConflict(Exception):
    """Someone changed the kitten since we read it (HTTP 409)."""


def connect(path: str) -> sqlite3.Connection:
    """Autocommit mode (isolation_level=None): you write BEGIN / COMMIT / ROLLBACK yourself.
    `timeout` is how long a writer waits for the lock held by another connection."""
    conn = sqlite3.connect(path, isolation_level=None, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def transfer_food(conn: sqlite3.Connection, source: str, target: str, kg: int) -> None:
    """Move `kg` from pantry `source` to pantry `target`, all or nothing.

    Contract:
    - one transaction opened with BEGIN IMMEDIATE (takes the write lock now, so two transfers
      cannot interleave), COMMIT on success, ROLLBACK on any error, then re-raise
    - debit with a guarded UPDATE: ... SET food_kg = food_kg - ? WHERE id = ? AND food_kg >= ?
      and look at rowcount. Never SELECT the stock, compute in Python, then UPDATE: that
      read-modify-write is exactly the race that loses food
    - debit refused: raise UnknownPantry if `source` does not exist, else InsufficientFood
    - credit the target and raise UnknownPantry if it does not exist (rowcount 0)
    """
    # TODO(level 07)
    raise NotImplementedError("transfer_food")


def adopt(conn: sqlite3.Connection, kitten_id: str, family: str, expected_version: int) -> int:
    """Optimistic locking: one compare-and-set UPDATE, no lock held while the family decides.

    Contract:
    - UPDATE ... SET adopted_by = ?, version = version + 1
      WHERE id = ? AND version = ? AND adopted_by IS NULL
    - rowcount 1 -> return the new version (expected_version + 1)
    - rowcount 0 -> raise AdoptionConflict (stale version, or already adopted)
    """
    # TODO(level 07)
    raise NotImplementedError("adopt")


def read_kitten(conn: sqlite3.Connection, kitten_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM kittens WHERE id = ?", (kitten_id,)).fetchone()
    if row is None:
        raise LookupError(kitten_id)
    return row


# Zero-downtime migration of kittens.name into a new kittens.slug column, in four deploys:
#   1. expand      add the nullable column, new code writes both columns   (expand_schema)
#   2. backfill    fill old rows in small batches, the table stays usable  (backfill_in_batches)
#   3. switch      new code reads slug
#   4. contract    once nothing reads the old shape, add NOT NULL / drop leftovers


def expand_schema(conn: sqlite3.Connection) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(kittens)")}
    if "slug" not in columns:
        conn.execute("ALTER TABLE kittens ADD COLUMN slug TEXT")


def backfill_in_batches(conn: sqlite3.Connection, batch_size: int) -> int:
    """Set slug = lower(name) where slug IS NULL, at most `batch_size` rows per statement.

    Contract:
    - each batch is its own short statement or transaction: never one giant UPDATE that
      locks the whole table for minutes
    - pick the batch with a subquery: WHERE id IN (SELECT id FROM kittens
      WHERE slug IS NULL LIMIT ?)
    - loop until a batch updates 0 rows, return how many batches updated at least one row
    - running it again when everything is filled returns 0 (safe to resume after a crash)
    """
    # TODO(level 07)
    raise NotImplementedError("backfill_in_batches")
