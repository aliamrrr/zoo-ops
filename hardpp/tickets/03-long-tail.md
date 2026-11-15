# PLANET-203 The long tail

**Area:** `zoo_planet.models`
**Pattern:** Hedged requests, concurrency limits, priority load shedding
**Asked at:** Google ("The Tail at Scale"), Amazon, Netflix

> The median kiosk answer takes 10 ms, but one in ten takes 300 ms because a replica is
> busy. At our scale, almost every visitor hits the slow one. During peaks a replica gets
> 40 requests at once and all of them become slow. When saturated, we would rather drop
> "is the shop open?" than "a child is lost at the gate".

## Requirements

1. **Hedging.** When a request has not answered after about the p95 latency (30 ms), send the same request to another replica and return the first answer. Only late requests are hedged: total replica calls stay within 25% of the requests.
2. **Concurrency limit.** A replica never runs more than **8** requests at once, hedges included.
3. **Load shedding.** When every replica is at its limit, `priority="low"` requests fail immediately with `Overloaded`. `"normal"` and `"high"` requests wait for a free slot.

## Constraints

- `ModelPool.ask(prompt, priority)` keeps its signature. `ModelReplica` is the model server: do not change it.
- No busy waiting.

## Done when

`python -m zoo test --mode hardpp 3` is green.

## Read before you start

- [The Tail at Scale, Dean and Barroso](https://research.google/pubs/the-tail-at-scale/)
- [Using load shedding to avoid overload, Amazon Builders' Library](https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/)
