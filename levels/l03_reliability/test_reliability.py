import random
from collections.abc import Iterable

import pytest

from levels.l03_reliability.reliability import (
    AllProvidersFailed,
    CircuitBreaker,
    FatalError,
    ProviderTimeout,
    RetryPolicy,
    TransientError,
    backoff_delay,
    complete_with_fallback,
    retry,
)
from zoo.kit import FakeClock


class ScriptedProvider:
    """Plays a script of outcomes: a string is an answer, an exception class is raised."""

    def __init__(self, name: str, script: Iterable[object]) -> None:
        self.name = name
        self._script = list(script)
        self.calls: list[float] = []

    def complete(self, prompt: str, timeout: float) -> str:
        self.calls.append(timeout)
        outcome = self._script.pop(0) if self._script else self._script_end()
        if isinstance(outcome, type) and issubclass(outcome, BaseException):
            raise outcome(f"{self.name} failed")
        return str(outcome)

    def _script_end(self) -> object:
        raise AssertionError(f"{self.name} was called more often than expected")


def policy(sleeps: list[float], attempts: int = 3) -> RetryPolicy:
    return RetryPolicy(
        attempts=attempts, base_delay=1.0, max_delay=8.0, sleep=sleeps.append, rng=random.Random(7)
    )


def test_backoff_grows_and_is_capped() -> None:
    rng = random.Random(1)
    for attempt, ceiling in [(0, 1.0), (1, 2.0), (2, 4.0), (3, 8.0), (10, 8.0)]:
        delays = [backoff_delay(attempt, base=1.0, cap=8.0, rng=rng) for _ in range(200)]
        assert all(0 <= d <= ceiling for d in delays)
        assert max(delays) > ceiling * 0.8, "full jitter should use the whole range"


def test_backoff_is_jittered() -> None:
    rng = random.Random(2)
    delays = {backoff_delay(3, base=1.0, cap=8.0, rng=rng) for _ in range(20)}
    assert len(delays) > 15, "without jitter every client retries at the same instant"


def test_retry_returns_after_transient_failures() -> None:
    sleeps: list[float] = []
    provider = ScriptedProvider("owl", [ProviderTimeout, ProviderTimeout, "hoot"])
    assert retry(lambda: provider.complete("q", 1.0), policy(sleeps)) == "hoot"
    assert len(provider.calls) == 3
    assert len(sleeps) == 2


def test_retry_gives_up_without_a_last_sleep() -> None:
    sleeps: list[float] = []
    provider = ScriptedProvider("owl", [ProviderTimeout] * 3)
    with pytest.raises(ProviderTimeout):
        retry(lambda: provider.complete("q", 1.0), policy(sleeps))
    assert len(provider.calls) == 3
    assert len(sleeps) == 2, "sleeping after the final failure only adds latency"


def test_retry_does_not_retry_fatal_errors() -> None:
    sleeps: list[float] = []
    provider = ScriptedProvider("owl", [FatalError])
    with pytest.raises(FatalError):
        retry(lambda: provider.complete("q", 1.0), policy(sleeps))
    assert len(provider.calls) == 1
    assert sleeps == []


def test_breaker_opens_after_threshold() -> None:
    breaker = CircuitBreaker(failure_threshold=3, reset_timeout=10, clock=FakeClock())
    for _ in range(2):
        breaker.record_failure()
    assert breaker.state == "closed" and breaker.allow_request()
    breaker.record_failure()
    assert breaker.state == "open"
    assert breaker.allow_request() is False


def test_breaker_success_resets_the_count() -> None:
    breaker = CircuitBreaker(failure_threshold=2, reset_timeout=10, clock=FakeClock())
    breaker.record_failure()
    breaker.record_success()
    breaker.record_failure()
    assert breaker.state == "closed", "only consecutive failures should open the breaker"


def test_breaker_half_open_then_closed() -> None:
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=1, reset_timeout=10, clock=clock)
    breaker.record_failure()
    clock.advance(9.9)
    assert breaker.allow_request() is False
    clock.advance(0.1)
    assert breaker.allow_request() is True
    assert breaker.state == "half_open"
    breaker.record_success()
    assert breaker.state == "closed"


def test_breaker_half_open_failure_reopens() -> None:
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=3, reset_timeout=10, clock=clock)
    for _ in range(3):
        breaker.record_failure()
    clock.advance(10)
    assert breaker.allow_request()
    breaker.record_failure()
    assert breaker.state == "open"
    clock.advance(5)
    assert breaker.allow_request() is False, "the open timer restarts after a failed trial"


def make_breakers(*names: str) -> dict[str, CircuitBreaker]:
    return {name: CircuitBreaker(2, 30, FakeClock()) for name in names}


def test_fallback_uses_the_backup_model() -> None:
    owl = ScriptedProvider("owl", [ProviderTimeout] * 3)
    parrot = ScriptedProvider("parrot", ["squawk"])
    breakers = make_breakers("owl", "parrot")
    result = complete_with_fallback("q", [owl, parrot], breakers, policy([]), timeout=2.5)
    assert result == ("parrot", "squawk")
    assert owl.calls == [2.5, 2.5, 2.5], "every attempt must carry the timeout"
    assert breakers["owl"]._failures == 1


def test_fallback_skips_open_breakers() -> None:
    owl = ScriptedProvider("owl", [])
    parrot = ScriptedProvider("parrot", ["squawk"])
    breakers = make_breakers("owl", "parrot")
    breakers["owl"].record_failure()
    breakers["owl"].record_failure()
    assert complete_with_fallback("q", [owl, parrot], breakers, policy([]), 1.0)[0] == "parrot"
    assert owl.calls == [], "an open breaker must protect the dead provider"


def test_fallback_raises_when_everyone_is_down() -> None:
    owl = ScriptedProvider("owl", [TransientError] * 3)
    parrot = ScriptedProvider("parrot", [TransientError] * 3)
    with pytest.raises(AllProvidersFailed):
        complete_with_fallback("q", [owl, parrot], make_breakers("owl", "parrot"), policy([]), 1.0)


def test_fallback_propagates_fatal_errors() -> None:
    owl = ScriptedProvider("owl", [FatalError])
    parrot = ScriptedProvider("parrot", [])
    with pytest.raises(FatalError):
        complete_with_fallback("q", [owl, parrot], make_breakers("owl", "parrot"), policy([]), 1.0)
    assert parrot.calls == []
