# 06 Database performance: The Burrows

**In the game.** Digby the mole browses the cat catalog page by page while new kittens keep arriving, prints an enclosure report, and shares a few database connections with 40 visitors. Every query is a tunnel.

## The pattern

- **Index for the query you run**: a composite index matching the `WHERE` then the `ORDER BY` lets the database walk rows already sorted. No full scan, no sort.
- **EXPLAIN**: read the plan instead of guessing. `SCAN` means full table, `USE TEMP B-TREE FOR ORDER BY` means an extra sort. Postgres says `Seq Scan` and `Sort`.
- **N+1 queries**: one query for a list, then one per item. Replace with a JOIN or a single `WHERE id IN (...)`.
- **Cursor (keyset) pagination**: continue after the last row seen, `WHERE (arrived_at, id) < (?, ?)`. Stable when rows are inserted, and fast at page 1000, unlike `OFFSET`.
- **Connection pooling**: reuse a few open connections instead of paying TCP, TLS and auth on every request. Bound the pool so the database is never flooded.

## What you write

In [db_performance.py](db_performance.py): `index_statements`, `catalog_page`, `animals_with_enclosure` (it works, but runs N+1 queries), `ConnectionPool.connection`.

## How it breaks in the game

| Bug | What you see |
| --- | --- |
| Missing or wrong index | The plan shows a full scan or a temporary sort |
| OFFSET pagination | Kittens served twice, others never listed |
| N+1 | 51 tunnels for 50 animals |
| Unbounded or leaking pool | More connections than the pool size, or visitors stuck |

## Learn it

- [We need tool support for keyset pagination (Use The Index, Luke)](https://use-the-index-luke.com/no-offset)
- [SQLite EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html)
- [Using EXPLAIN (PostgreSQL)](https://www.postgresql.org/docs/current/using-explain.html)

## Hints

- Fetch `limit + 1` rows: if you got the extra one, there is a next page.
- The cursor is the `(arrived_at, id)` of the last item served, `encode_cursor` is provided.
- Pool: `get_nowait()` an idle one, else create while under `size` (under the lock), else `get(timeout=...)`. Return it in a `finally`.

```
python -m zoo test 6
python -m zoo scene 6
```
