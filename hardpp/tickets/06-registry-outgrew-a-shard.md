# PLANET-206 The registry outgrew its shards

**Area:** `zoo_planet.storage`
**Pattern:** Sharding: consistent hashing, online resharding, scatter-gather
**Asked at:** Google (Spanner), Amazon (DynamoDB), Uber (Schemaless)

> The animal registry is split over 4 database shards by `hash(id) % 4`. We need a fifth.
> Adding it today would move 80% of the rows, during which reads fail. The "newest
> arrivals" page reads every row of every shard to show 20 animals.

## Requirements

1. Owners are assigned on a **consistent hash ring with virtual nodes**: adding a shard moves at most 30% of the keys, only to the new shard, and keys stay evenly spread.
2. **Online resharding.** After `add_shard`, repeated calls to `rebalance(batch)` move misplaced records to their owner, at most `batch` per call, and return how many moved (0 when done). During the whole migration every `get` finds every record, and a `put` made during the migration is never overwritten by an old copy. At the end each record lives only on its owner.
3. **Scatter-gather.** `newest(species, limit, cursor)` returns the global order (newest arrival first, then id) and an opaque cursor, reading at most `limit + 1` rows from each shard per page.

## Constraints

- `Shard` is the database server: do not change it. Its `newest(species, limit, before)` is served by an index.

## Done when

`python -m zoo test --mode hardpp 6` is green.

## Read before you start

- [Dynamo: Amazon's highly available key-value store (partitioning, section 4.2)](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)
- [Designing Data-Intensive Applications, chapter 6: Partitioning](https://dataintensive.net/)
