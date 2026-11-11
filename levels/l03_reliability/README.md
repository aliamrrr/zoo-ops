# 03 Reliability of external calls: The Bridge

**In the game.** Rusty the fox carries questions across the bridge to the Owl. A 90 second storm makes the Owl unreachable. The Parrot, a smaller model, is the backup.

## The pattern

- **Timeout**: every attempt has a deadline. Waiting forever turns one slow dependency into a full outage.
- **Retry with exponential backoff and full jitter**: transient errors (timeout, 429, 503) get a few more attempts, spaced `uniform(0, min(cap, base * 2^n))`. Jitter keeps a thousand clients from retrying in sync.
- **Only retry what can succeed**: a 400 will fail again, retrying it only adds load.
- **Circuit breaker**: after N failures in a row, stop calling the dependency for a while (open), then let one trial request through (half-open). Success closes it, failure reopens it.
- **Fallback**: when a provider is down or its breaker is open, try the next one.

## What you write

In [reliability.py](reliability.py): `backoff_delay`, `retry`, `CircuitBreaker.allow_request`, `CircuitBreaker.record_success`, `CircuitBreaker.record_failure`, `complete_with_fallback`.

## How it breaks in the game

| Bug | What you see |
| --- | --- |
| No fallback | Visitors get no answer during the storm |
| No breaker | Rusty hammers the dead Owl dozens of times |
| Unbounded retries or sleeps | A visitor waits far longer than a few timeouts |
| Half-open never recovers | The storm is over but the Owl never gets traffic back |

## Learn it

- [Timeouts, retries and backoff with jitter (Amazon Builders' Library)](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)
- [Exponential backoff and jitter (AWS Architecture Blog)](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
- [CircuitBreaker (Martin Fowler)](https://martinfowler.com/bliki/CircuitBreaker.html)

## Hints

- `retry` is a `for attempt in range(policy.attempts)` loop with `try` / `except TransientError`.
- The breaker only needs a state, a failure counter and the time it opened.
- `functools.partial(provider.complete, prompt, timeout)` is an operation `retry` can call.

```
python -m zoo test 3
python -m zoo scene 3
```
