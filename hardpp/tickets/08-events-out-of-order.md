# PLANET-208 Events out of order

**Area:** `zoo_planet.stream`
**Pattern:** Partitioned log: per-key ordering, consumer groups, rebalancing
**Asked at:** LinkedIn (Kafka), Uber, Confluent

> Leo's "fed" event was processed before his "food prepared" event. When a consumer joins,
> it gets nothing to do; when one crashes, its partitions are orphaned. Offsets are
> committed before processing, so a crash loses events. A consumer that came back after a
> long pause committed offsets for a partition it no longer owned.

## Requirements

1. Events with the same key always go to the same partition, so they are consumed in order.
2. `join` and `leave` rebalance the group: every partition has exactly one owner among the current members, and owners have the same number of partitions give or take one.
3. `poll(member)` returns uncommitted records of the member's partitions without committing them. The consumer calls `commit(member, partition, next_offset)` after processing. A crash before the commit means the records are delivered again, in order, to whoever owns the partition next.
4. A commit from a member that does not own the partition is refused with an exception whose message says the member is not the owner.

## Done when

`python -m zoo test --mode hardpp 8` is green.

## Read before you start

- [Kafka documentation: consumer groups and offsets](https://kafka.apache.org/documentation/#intro_consumers)
- [The Log: what every software engineer should know, Jay Kreps](https://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying)
