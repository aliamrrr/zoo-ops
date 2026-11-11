# 07 Data integrity: The Dam

**In the game.** Bea the beaver keeps the books. Six keepers move food between pantries at the same time, two families click "adopt Pixel" in the same millisecond, and a column migrates while the zoo stays open.

## The pattern

- **Transactions**: several writes succeed together or not at all. Roll back on any error.
- **Race conditions**: `SELECT stock`, compute in Python, `UPDATE stock = new_value` loses updates when two requests interleave. Do the arithmetic in one guarded statement: `UPDATE ... SET x = x - ? WHERE id = ? AND x >= ?`, then check `rowcount`.
- **Locks**: `BEGIN IMMEDIATE` (SQLite) or `SELECT ... FOR UPDATE` (Postgres) takes the write lock before reading, so the next transaction waits.
- **Optimistic locking**: a `version` column. Update only `WHERE version = expected`, bump it, and treat 0 rows as a conflict (409). No lock is held while a human decides.
- **Zero-downtime migrations (expand and contract)**: add the new nullable column, write both, backfill in small batches, switch reads, and only then drop or constrain. Every step works with the previous code version.

## What you write

In [integrity.py](integrity.py): `transfer_food`, `adopt`, `backfill_in_batches`.

## How it breaks in the game

| Bug | What you see |
| --- | --- |
| Read-modify-write | Kilos of food appear or vanish |
| No rollback | A debit without its credit |
| No version check | Two families both think they adopted Pixel |
| One giant UPDATE | The backfill runs as one batch and locks the table |

## Learn it

- [SQLite transactions, BEGIN IMMEDIATE](https://www.sqlite.org/lang_transaction.html)
- [Explicit locking (PostgreSQL)](https://www.postgresql.org/docs/current/explicit-locking.html)
- [ParallelChange, a.k.a. expand and contract (Martin Fowler)](https://martinfowler.com/bliki/ParallelChange.html)

## Hints

- The connection is in autocommit mode: `conn.execute("BEGIN IMMEDIATE")`, `"COMMIT"`, `"ROLLBACK"` are yours.
- Distinguish an unknown pantry from an empty one with a tiny `SELECT 1` only after the guarded update failed.
- The backfill loop ends when `rowcount == 0`.

```
python -m zoo test 7
python -m zoo scene 7
```
