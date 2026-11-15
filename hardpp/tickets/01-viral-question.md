# PLANET-201 The viral question

**Area:** `zoo_planet.cache`
**Pattern:** Cache stampede protection, stale-while-revalidate, consistent hashing
**Asked at:** Meta (memcache lease paper), Google, Netflix (EVCache)

> A video of a pink flamingo went viral. Forty thousand visitors asked the same question
> within a second of its answer expiring, and every cache miss went to the model fleet at
> once. The fleet fell over, and so did every question behind it. The same evening, adding
> one cache node to absorb the load emptied most of the cache.

## Requirements

1. **Coalescing.** Concurrent misses for the same question call the model **once**. Every caller gets that one answer. Different questions do not wait for each other.
2. **Stale while revalidate.** When an answer has expired **less than 120 seconds ago**, callers get the stale answer immediately while **one** background refresh runs. Older answers are not served.
3. **Consistent hashing.** Adding a node to a cluster of N moves only about 1/(N+1) of the keys, and only to the new node. Load stays even across nodes (use virtual nodes).

## Constraints

- `AnswerService.answer(question)` and `CacheCluster.node_for(key)` / `add_node(node)` keep their signatures.
- Time comes from the nodes' clock, never from `time.time()`.

## Done when

`python -m zoo test --mode hardpp 1` is green.

## Read before you start

- [Scaling Memcache at Facebook (leases, section 3.2.1)](https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf)
- [Consistent hashing, Karger et al.](https://www.akamai.com/site/en/documents/research-paper/consistent-hashing-and-random-trees-distributed-caching-protocols-for-relieving-hot-spots-on-the-world-wide-web-technical-publication.pdf)
- [Optimal probabilistic cache stampede prevention](https://cseweb.ucsd.edu/~avattani/papers/cache_stampede.pdf)
