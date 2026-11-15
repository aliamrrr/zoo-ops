# ZOO-103 The storm on the bridge

**Reporter:** Site reliability
**Pattern:** Reliability of external calls

> Yesterday the model provider had a 40 minute partial outage. Our workers waited on
> calls that never returned, the thread pool filled up, and the whole platform stopped
> answering, including the kitchen and the adoption office. We pay for a smaller backup
> model ("parrot") that nobody wired in.

## Acceptance criteria

- Every call to a model carries a deadline of at most **3 seconds**.
- A transient failure (`ProviderUnavailable`) is retried, up to **3 attempts in total**, waiting between attempts with exponential backoff and full jitter: a random wait between 0 and `min(2, 0.2 * 2^n)` seconds before retry number `n + 1` (n starts at 0).
- Waiting goes through the platform's sleeper, never `time.sleep` directly, so tests and simulations control time.
- When the primary model still fails, the question is answered by the backup model (`Settings.parrot_model`) and the response says which model answered.
- After **3 consecutive failed questions** on a model, stop calling that model for **30 seconds**. After that, let one question through: success closes the circuit, failure opens it for another 30 seconds. Each model has its own circuit, so a broken model version cannot block a healthy one.
- A permanent failure (`ProviderRejected`) answers `422` at once: no retry, no backup.

## Done when

`python -m zoo test --mode hard 3` is green and the unit tests still pass.

## Read before you start

- [Timeouts, retries and backoff with jitter, Amazon Builders' Library](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)
- [CircuitBreaker, Martin Fowler](https://martinfowler.com/bliki/CircuitBreaker.html)
