"""Level 03: timeouts, retries with backoff and jitter, circuit breaker, model fallback.

Every call to an external service (an LLM provider, a payment API) can be slow, fail for a
moment, or be down for minutes. The layers, from inside out:
    timeout          never wait forever: the provider gets `timeout` seconds per attempt
    retry            transient errors get a few more attempts, spaced by backoff with jitter
    circuit breaker  after repeated failures, stop calling a dead provider for a while
    fallback         ask the next provider in the list (a smaller model is better than nothing)
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal, Protocol, TypeVar

T = TypeVar("T")
Clock = Callable[[], float]
BreakerState = Literal["closed", "open", "half_open"]


class TransientError(Exception):
    """Worth retrying: timeout, HTTP 429, HTTP 503."""


class ProviderTimeout(TransientError):
    pass


class FatalError(Exception):
    """Not worth retrying: HTTP 400, HTTP 401, a prompt the model rejects."""


class AllProvidersFailed(Exception):
    pass


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 3
    base_delay: float = 0.2
    max_delay: float = 5.0
    sleep: Callable[[float], None] = time.sleep
    rng: random.Random = field(default_factory=random.Random)

    def __post_init__(self) -> None:
        if self.attempts < 1:
            raise ValueError("attempts counts the first call, it must be at least 1")


def backoff_delay(attempt: int, base: float, cap: float, rng: random.Random) -> float:
    """Exponential backoff with full jitter, `attempt` starting at 0:
    a uniform random delay between 0 and min(cap, base * 2 ** attempt).
    The jitter spreads retries so a thousand clients do not hit the provider in sync."""
    # TODO(level 03)
    raise NotImplementedError("backoff_delay")


def retry(operation: Callable[[], T], policy: RetryPolicy) -> T:
    """Call `operation` up to `policy.attempts` times.

    Contract:
    - TransientError: sleep backoff_delay(attempt, ...) via policy.sleep, then try again
    - the last TransientError is re-raised once attempts are exhausted, with no sleep after it
    - any other exception propagates immediately, without sleeping
    """
    # TODO(level 03)
    raise NotImplementedError("retry")


class CircuitBreaker:
    """closed --(failure_threshold failures in a row)--> open
    open   --(reset_timeout seconds elapsed, next allow_request)--> half_open
    half_open --success--> closed      half_open --failure--> open (timer restarts)
    """

    def __init__(self, failure_threshold: int, reset_timeout: float, clock: Clock) -> None:
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._clock = clock
        self.state: BreakerState = "closed"
        self._failures = 0
        self._opened_at = 0.0

    def allow_request(self) -> bool:
        """closed and half_open allow. open refuses, unless reset_timeout has elapsed since it
        opened: then switch to half_open and allow this one trial request."""
        # TODO(level 03)
        raise NotImplementedError("CircuitBreaker.allow_request")

    def record_success(self) -> None:
        """Back to closed, failure count reset."""
        # TODO(level 03)
        raise NotImplementedError("CircuitBreaker.record_success")

    def record_failure(self) -> None:
        """Count the failure. Open (and remember when) when the threshold is reached,
        or immediately when the trial request of half_open fails."""
        # TODO(level 03)
        raise NotImplementedError("CircuitBreaker.record_failure")


class Provider(Protocol):
    name: str

    def complete(self, prompt: str, timeout: float) -> str: ...


def complete_with_fallback(
    prompt: str,
    providers: Sequence[Provider],
    breakers: Mapping[str, CircuitBreaker],
    policy: RetryPolicy,
    timeout: float,
) -> tuple[str, str]:
    """Return (provider name, answer) from the first provider able to answer.

    Contract, for each provider in order:
    - skip it when its breaker (breakers[provider.name]) does not allow the request
    - call provider.complete(prompt, timeout) through retry()
    - answer -> breaker.record_success() and return
    - TransientError after all retries -> breaker.record_failure(), try the next provider
    - FatalError propagates: another model will not fix a bad request
    Nobody answered -> raise AllProvidersFailed.
    Tip: functools.partial(provider.complete, prompt, timeout) is a ready-made operation.
    """
    # TODO(level 03)
    raise NotImplementedError("complete_with_fallback")
