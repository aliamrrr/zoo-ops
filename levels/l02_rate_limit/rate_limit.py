"""Level 02: token-bucket rate limiting per API key, counted in requests and in LLM tokens.

A token bucket holds at most `capacity` tokens and refills continuously at `refill_per_second`.
A request costs some tokens: enough tokens means admitted, otherwise rejected with a Retry-After.
Bursts up to `capacity` are allowed, the long-run rate is capped at the refill rate.

In production the bucket state lives in Redis and is updated atomically by a Lua script, so every
gateway replica shares the same budget. The arithmetic below is exactly the same.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

Clock = Callable[[], float]


class TokenBucket:
    """Starts full. `clock` returns seconds (time.monotonic in production, a FakeClock in tests)."""

    def __init__(self, capacity: float, refill_per_second: float, clock: Clock) -> None:
        if capacity <= 0 or refill_per_second <= 0:
            raise ValueError("capacity and refill_per_second must be positive")
        self.capacity = capacity
        self.refill_per_second = refill_per_second
        self._clock = clock
        self._tokens = capacity
        self._updated_at = clock()

    @property
    def tokens(self) -> float:
        self._refill()
        return self._tokens

    def _refill(self) -> None:
        """Add the tokens earned since `_updated_at` (never above capacity), then move
        `_updated_at` to now."""
        # TODO(level 02): elapsed time * refill rate, capped at capacity.
        raise NotImplementedError("TokenBucket.refill")

    def try_consume(self, amount: float = 1.0) -> bool:
        """Refill, then take `amount` tokens if they are all there. A refusal takes nothing."""
        # TODO(level 02)
        raise NotImplementedError("TokenBucket.try_consume")

    def retry_after(self, amount: float = 1.0) -> float:
        """Seconds until `amount` tokens are available: 0.0 if available now, math.inf if
        `amount` is larger than the capacity (it will never fit)."""
        # TODO(level 02)
        raise NotImplementedError("TokenBucket.retry_after")


@dataclass(frozen=True)
class Plan:
    requests_per_minute: int
    tokens_per_minute: int


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str | None = None
    retry_after: float = 0.0


class RateLimiter:
    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._buckets: dict[str, tuple[TokenBucket, TokenBucket]] = {}

    def buckets_for(self, api_key: str, plan: Plan) -> tuple[TokenBucket, TokenBucket]:
        """(request bucket, token bucket) of this key, created full on first use."""
        if api_key not in self._buckets:
            requests = TokenBucket(
                plan.requests_per_minute, plan.requests_per_minute / 60, self._clock
            )
            tokens = TokenBucket(plan.tokens_per_minute, plan.tokens_per_minute / 60, self._clock)
            self._buckets[api_key] = (requests, tokens)
        return self._buckets[api_key]

    def check(self, api_key: str, plan: Plan, llm_tokens: int) -> Decision:
        """Admit one request costing 1 request and `llm_tokens` tokens.

        Contract:
        - every API key has its own two buckets (see `buckets_for`)
        - admitted only if BOTH buckets can pay, and then both are charged
        - a rejected request charges nothing at all (no partial consumption)
        - rejected: reason is "requests" or "tokens" (requests checked first) and
          retry_after comes from the bucket that refused
        """
        # TODO(level 02): peek both buckets with retry_after, then consume.
        raise NotImplementedError("RateLimiter.check")


def estimate_tokens(text: str) -> int:
    """Rough rule of thumb: one token is about four characters of English."""
    return max(1, len(text) // 4)


@dataclass(frozen=True)
class GatewayRequest:
    api_key: str | None
    model: str
    prompt: str


@dataclass(frozen=True)
class GatewayResponse:
    status: int
    body: str
    headers: dict[str, str]


class Gateway:
    """What Nginx, Kong or a LiteLLM proxy does in front of the models: authenticate the key,
    apply its plan, route the model name to an upstream. See nginx.conf and litellm_config.yaml."""

    def __init__(
        self,
        keys: dict[str, Plan],
        routes: dict[str, Callable[[str], str]],
        limiter: RateLimiter,
    ) -> None:
        self._keys = keys
        self._routes = routes
        self._limiter = limiter

    def handle(self, request: GatewayRequest) -> GatewayResponse:
        plan = self._keys.get(request.api_key or "")
        if request.api_key is None or plan is None:
            return GatewayResponse(401, "unknown API key", {})
        upstream = self._routes.get(request.model)
        if upstream is None:
            return GatewayResponse(404, f"no route for model {request.model!r}", {})
        decision = self._limiter.check(request.api_key, plan, estimate_tokens(request.prompt))
        if not decision.allowed:
            retry_after = decision.retry_after
            header = "86400" if math.isinf(retry_after) else str(math.ceil(retry_after))
            body = f"rate limited on {decision.reason}"
            return GatewayResponse(429, body, {"Retry-After": header})
        return GatewayResponse(200, upstream(request.prompt), {})
