# PLANET-204 Billed twice, or never

**Area:** `zoo_planet.orders`
**Pattern:** Transactional outbox + idempotent consumer (exactly-once effects)
**Asked at:** Uber, Amazon, Shopify

> The orders service writes an order, then publishes an event to the broker. When it
> crashes in between, the order exists but billing never hears about it. The broker
> delivers at least once, so when billing crashes before acknowledging a message, the
> family is charged twice.

## Requirements

1. An order and its event are written **atomically**: if the order commits, its event will be published, even if the process crashes right after the commit. If the order rolls back, nothing is published.
2. Create `zoo_planet/orders/outbox.py` with `OutboxRelay(db, broker, crash)` and `run_once() -> int` (the number of events published in this run). The relay may publish an event more than once.
3. The relay calls `crash.point("relay.after_publish")` right after publishing an event and before recording that it did.
4. Billing applies each event **exactly once**, whatever the redeliveries and republishes.
5. Keep the crash points that exist: `order.after_commit` and `billing.after_charge`.

## Constraints

- The broker has no transactions. The two databases cannot join a distributed transaction.

## Done when

`python -m zoo test --mode hardpp 4` is green.

## Read before you start

- [Pattern: Transactional outbox, microservices.io](https://microservices.io/patterns/data/transactional-outbox.html)
- [Pattern: Idempotent consumer, microservices.io](https://microservices.io/patterns/communication-style/idempotent-consumer.html)
