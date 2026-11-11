# 04 Idempotency: The Food Bowl

**In the game.** Miso the cat orders three 50 g meals over a network that loses responses. The client retries every request three times. Without idempotency, Miso eats 450 g.

## The pattern

- **Idempotency-Key**: the client generates one key per logical operation and sends it on every retry. The server stores the key with the response and replays it instead of doing the work again.
- **Fingerprint**: the key is bound to a hash of the payload. The same key with another payload is a client bug: 422.
- **In progress**: a second request arriving while the first still runs gets a 409, never a second execution.
- **Release on failure**: if the work failed, the key is freed so a retry can run.
- **Database guard**: a UNIQUE business key (`order_id`) with `INSERT ... ON CONFLICT DO NOTHING` protects against every writer that bypasses the API, like a batch job. Upserts (`ON CONFLICT DO UPDATE`) make counters safe.

## What you write

In [idempotency.py](idempotency.py): `fingerprint`, `IdempotencyStore.execute`, `record_meal`.

## How it breaks in the game

| Bug | What you see |
| --- | --- |
| Handler runs on every retry | Miso eats 450 g and rolls instead of walking |
| No UNIQUE guard in the DB | A nightly batch replays the orders and doubles the belly |
| Key not bound to payload | A 5 kg order sneaks in under an old key |

## Learn it

- [Designing robust and predictable APIs with idempotency (Stripe)](https://stripe.com/blog/idempotency)
- [Implementing Stripe-like idempotency keys in Postgres (Brandur Leach)](https://brandur.org/idempotency-keys)
- [SQLite UPSERT](https://www.sqlite.org/lang_upsert.html) (same syntax as Postgres)

## Hints

- `cursor.rowcount` after `INSERT ... ON CONFLICT DO NOTHING` is 1 when you inserted, 0 when the row existed. That is an atomic "claim".
- The claim must be committed before running the handler, or a concurrent request cannot see it.
- `with transaction(conn):` gives you BEGIN, COMMIT and ROLLBACK.

```
python -m zoo test 4
python -m zoo scene 4
```
