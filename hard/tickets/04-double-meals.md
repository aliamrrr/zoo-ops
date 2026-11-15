# ZOO-104 Animals are fed twice

**Reporter:** Head vet
**Pattern:** Idempotency

> Miso the cat had to be put on a diet. The keepers' tablets lose their connection in the
> big cat house and resend the meal order, and each retry feeds the animal again. The food
> supplier also replays its delivery batches when their side times out.

## Acceptance criteria

- `POST /v1/kitchen/orders` accepts an optional `Idempotency-Key` header.
- Retrying with the same key and the same body returns the **same status and body** as the first call, adds the header `Idempotent-Replayed: true`, and feeds the animal once.
- The same key with a different body is refused with `422`.
- While the first request with a key is still running, a concurrent one with that key gets `409` and feeds nothing.
- Keys belong to their caller: two keepers who happen to pick the same key do not see each other's orders.
- A failed request does not lock its key: the client can retry it.
- Supplier deliveries (`POST /v1/kitchen/supplier-deliveries`) are counted **once per `reference`**, forever, even across batches and replicas. The response's `accepted` counts only new deliveries.
- Requests without a key keep working as today.

## Done when

`python -m zoo test --mode hard 4` is green and the unit tests still pass.

## Read before you start

- [Designing robust and predictable APIs with idempotency, Stripe](https://stripe.com/blog/idempotency)
- [Implementing Stripe-like idempotency keys in Postgres, Brandur Leach](https://brandur.org/idempotency-keys)
- [SQLite UPSERT](https://www.sqlite.org/lang_upsert.html)
