import math

import pytest

from levels.l02_rate_limit.rate_limit import (
    Gateway,
    GatewayRequest,
    Plan,
    RateLimiter,
    TokenBucket,
)
from zoo.kit import FakeClock


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


def test_bucket_starts_full_and_empties(clock: FakeClock) -> None:
    bucket = TokenBucket(capacity=3, refill_per_second=1, clock=clock)
    assert [bucket.try_consume() for _ in range(4)] == [True, True, True, False]


def test_bucket_refills_with_time(clock: FakeClock) -> None:
    bucket = TokenBucket(capacity=2, refill_per_second=2, clock=clock)
    bucket.try_consume(2)
    clock.advance(0.5)
    assert bucket.try_consume() is True
    assert bucket.try_consume() is False


def test_bucket_never_exceeds_capacity(clock: FakeClock) -> None:
    bucket = TokenBucket(capacity=5, refill_per_second=10, clock=clock)
    clock.advance(3600)
    assert bucket.tokens == pytest.approx(5)


def test_refused_consume_takes_nothing(clock: FakeClock) -> None:
    bucket = TokenBucket(capacity=3, refill_per_second=1, clock=clock)
    assert bucket.try_consume(5) is False
    assert bucket.try_consume(3) is True


def test_retry_after(clock: FakeClock) -> None:
    bucket = TokenBucket(capacity=4, refill_per_second=2, clock=clock)
    assert bucket.retry_after(1) == 0.0
    bucket.try_consume(4)
    assert bucket.retry_after(1) == pytest.approx(0.5)
    assert bucket.retry_after(3) == pytest.approx(1.5)
    assert math.isinf(bucket.retry_after(10))


def test_keys_have_separate_budgets(clock: FakeClock) -> None:
    limiter = RateLimiter(clock)
    plan = Plan(requests_per_minute=2, tokens_per_minute=10_000)
    assert limiter.check("pigeon", plan, 10).allowed
    assert limiter.check("pigeon", plan, 10).allowed
    assert not limiter.check("pigeon", plan, 10).allowed
    assert limiter.check("hedgehog", plan, 10).allowed, "one spammer must not starve others"


def test_request_budget_rejection(clock: FakeClock) -> None:
    limiter = RateLimiter(clock)
    plan = Plan(requests_per_minute=1, tokens_per_minute=10_000)
    limiter.check("pigeon", plan, 10)
    decision = limiter.check("pigeon", plan, 10)
    assert decision.allowed is False
    assert decision.reason == "requests"
    assert decision.retry_after == pytest.approx(60)


def test_token_budget_rejection_charges_nothing(clock: FakeClock) -> None:
    limiter = RateLimiter(clock)
    plan = Plan(requests_per_minute=2, tokens_per_minute=1_000)
    decision = limiter.check("python", plan, 5_000)
    assert decision.allowed is False
    assert decision.reason == "tokens"
    requests, tokens = limiter.buckets_for("python", plan)
    assert requests.tokens == pytest.approx(2), "a rejected request must not use the request budget"
    assert tokens.tokens == pytest.approx(1_000)


def test_admitted_request_charges_both_budgets(clock: FakeClock) -> None:
    limiter = RateLimiter(clock)
    plan = Plan(requests_per_minute=10, tokens_per_minute=1_000)
    assert limiter.check("hedgehog", plan, 300).allowed
    requests, tokens = limiter.buckets_for("hedgehog", plan)
    assert requests.tokens == pytest.approx(9)
    assert tokens.tokens == pytest.approx(700)


def test_gateway_returns_429_with_retry_after(clock: FakeClock) -> None:
    gateway = Gateway(
        keys={"k1": Plan(requests_per_minute=1, tokens_per_minute=1_000)},
        routes={"owl": lambda prompt: "hoot"},
        limiter=RateLimiter(clock),
    )
    assert gateway.handle(GatewayRequest("k1", "owl", "hi")).status == 200
    limited = gateway.handle(GatewayRequest("k1", "owl", "hi"))
    assert limited.status == 429
    assert limited.headers["Retry-After"] == "60"
    assert gateway.handle(GatewayRequest("nope", "owl", "hi")).status == 401
