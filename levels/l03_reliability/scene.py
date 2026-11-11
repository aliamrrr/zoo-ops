"""Scene 03: a storm cuts the bridge to the Owl for 90 seconds. The Parrot is the backup."""

from __future__ import annotations

import random
from collections import Counter

from levels.l03_reliability.reliability import (
    AllProvidersFailed,
    CircuitBreaker,
    ProviderTimeout,
    RetryPolicy,
    complete_with_fallback,
)
from zoo.kit import FakeClock, Scene

STORM_ENDS_AT = 1_090.0
TIMEOUT = 2.0
REQUESTS = 80
SECONDS_BETWEEN_REQUESTS = 1.0


class StormyOwl:
    name = "owl"

    def __init__(self, clock: FakeClock) -> None:
        self._clock = clock
        self.wasted_attempts = 0

    def complete(self, prompt: str, timeout: float) -> str:
        if self._clock() < STORM_ENDS_AT:
            self.wasted_attempts += 1
            self._clock.advance(min(timeout, 60.0))
            raise ProviderTimeout("the bridge is under water")
        self._clock.advance(0.4)
        return "A wise and detailed hoot."


class Parrot:
    name = "parrot"

    def __init__(self, clock: FakeClock) -> None:
        self._clock = clock

    def complete(self, prompt: str, timeout: float) -> str:
        self._clock.advance(0.1)
        return "Squawk! Short answer."


def play(scene: Scene) -> None:
    clock = FakeClock()
    owl, parrot = StormyOwl(clock), Parrot(clock)
    breakers = {
        "owl": CircuitBreaker(failure_threshold=3, reset_timeout=20, clock=clock),
        "parrot": CircuitBreaker(failure_threshold=3, reset_timeout=20, clock=clock),
    }
    policy = RetryPolicy(
        attempts=3, base_delay=0.2, max_delay=2.0, sleep=clock.sleep, rng=random.Random(3)
    )

    answered_by = Counter[str]()
    worst_wait = 0.0
    last_provider = ""
    for _ in range(REQUESTS):
        started = clock()
        try:
            last_provider, _ = complete_with_fallback(
                "Tell me about otters", [owl, parrot], breakers, policy, TIMEOUT
            )
            answered_by[last_provider] += 1
        except AllProvidersFailed:
            answered_by["nobody"] += 1
        worst_wait = max(worst_wait, clock() - started)
        clock.advance(SECONDS_BETWEEN_REQUESTS)

    scene.info(f"{REQUESTS} visitors cross the bridge, the Owl is unreachable for 90 seconds.")
    scene.metric("answered by owl", answered_by["owl"])
    scene.metric("answered by parrot", answered_by["parrot"])
    scene.metric("unanswered", answered_by["nobody"])
    scene.metric("calls lost in the storm", owl.wasted_attempts)
    scene.metric("worst wait", f"{worst_wait:.1f} s")

    scene.check(
        answered_by["nobody"] == 0,
        "Every visitor got an answer: the Parrot covered for the Owl during the storm.",
        f"{answered_by['nobody']} visitors got no answer at all. No fallback?",
    )
    scene.check(
        owl.wasted_attempts <= 20,
        f"The breaker opened: only {owl.wasted_attempts} calls were wasted on the dead Owl.",
        f"Rusty hammered the dead Owl {owl.wasted_attempts} times. The breaker never opened.",
    )
    scene.check(
        worst_wait <= 3 * TIMEOUT + 2 * policy.max_delay,
        f"Timeouts bound the wait: nobody waited more than {worst_wait:.1f} s.",
        f"A visitor waited {worst_wait:.1f} s. Timeouts or retries are unbounded.",
    )
    scene.check(
        last_provider == "owl",
        "After the storm, a half-open probe found the Owl again and traffic went back to it.",
        "The storm is over but the Owl never got traffic back. Half-open never recovers?",
    )
