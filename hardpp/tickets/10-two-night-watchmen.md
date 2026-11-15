# PLANET-210 Two night watchmen

**Area:** `zoo_planet.coordination`
**Pattern:** Leader election with leases and fencing tokens
**Asked at:** Google (Chubby), Amazon, Uber

> The nightly feeding runs on three scheduler instances for availability, and all three
> feed the animals. When we tried a lease, a scheduler froze in a 15 second GC pause, lost
> its lease, a second one took over, then the first woke up and fed everyone again.

## Requirements

1. `LeaseStore.acquire(name, owner, ttl_s)` grants the lease only when nobody else holds an unexpired one. The holder renews by acquiring again. Each new grant returns a **fencing token** strictly greater than every token granted before.
2. Only one scheduler feeds per tick. When the leader stops ticking, another one takes over once the lease expires.
3. The ledger refuses a write whose token is lower than one it already accepted, or that has no token, with an exception saying the token is stale.

## Done when

`python -m zoo test --mode hardpp 10` is green.

## Read before you start

- [How to do distributed locking, Martin Kleppmann (fencing tokens)](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html)
- [The Chubby lock service, Mike Burrows](https://research.google/pubs/the-chubby-lock-service-for-loosely-coupled-distributed-systems/)
