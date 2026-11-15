# PLANET-202 One limit for the whole planet

**Area:** `zoo_planet.edge`
**Pattern:** Distributed rate limiting (GCRA) with compare-and-set
**Asked at:** Stripe, Cloudflare, Uber

> Partners pay for 100 questions a minute. A partner discovered that our three regions
> count separately, so they get 300. Another one hits us with 100 requests at 12:00:59
> and 100 more at 12:01:00. And one of our regions runs with a clock 25 seconds late.

## Requirements

1. A caller gets at most **100 admitted requests per rolling minute across all regions together**, even when every region is hammered concurrently.
2. No double burst at a minute boundary: the limit is a smooth rate (one new request every 0.6 s once the burst is spent), not a counter that resets.
3. Region clocks may be off by tens of seconds. The result must not depend on them.
4. Callers never share a budget.

## Constraints

- `Gateway.admit(caller) -> bool` keeps its signature.
- The only state shared between regions is the `SharedStore`. It is strongly consistent, offers `get`, `compare_and_set` and its own `now()`. No locks shared between regions.

## Done when

`python -m zoo test --mode hardpp 2` is green.

## Read before you start

- [GCRA, the generic cell rate algorithm, explained (Brandur Leach)](https://brandur.org/rate-limiting)
- [How we built rate limiting capable of scaling to millions of domains, Cloudflare](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/)
