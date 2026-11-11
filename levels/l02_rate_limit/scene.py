"""Scene 02: a pigeon flock floods the gate while a hedgehog just wants one answer per second."""

from __future__ import annotations

from collections import Counter

from levels.l02_rate_limit.rate_limit import Gateway, GatewayRequest, Plan, RateLimiter
from zoo.kit import FakeClock, Scene

PLAN = Plan(requests_per_minute=60, tokens_per_minute=6_000)
SECONDS = 10
PIGEON_RPS = 50


def play(scene: Scene) -> None:
    clock = FakeClock()
    owl_load = Counter[str]()

    def owl(prompt: str) -> str:
        owl_load["owl"] += 1
        return "hoot"

    gateway = Gateway(
        keys={"pigeon-flock": PLAN, "hedgehog": PLAN, "python": PLAN},
        routes={"owl": owl},
        limiter=RateLimiter(clock),
    )

    statuses: dict[str, Counter[int]] = {"pigeon-flock": Counter(), "hedgehog": Counter()}
    for _ in range(SECONDS):
        for _ in range(PIGEON_RPS):
            response = gateway.handle(GatewayRequest("pigeon-flock", "owl", "coo coo"))
            statuses["pigeon-flock"][response.status] += 1
        response = gateway.handle(GatewayRequest("hedgehog", "owl", "Where are the worms?"))
        statuses["hedgehog"][response.status] += 1
        clock.advance(1)

    pigeons_in = statuses["pigeon-flock"][200]
    hedgehog_in = statuses["hedgehog"][200]
    scene.info(f"In {SECONDS}s the pigeons send {SECONDS * PIGEON_RPS} requests.")
    scene.metric("pigeons admitted", pigeons_in)
    scene.metric("pigeons throttled (429)", statuses["pigeon-flock"][429])
    scene.metric("hedgehog served", f"{hedgehog_in}/{SECONDS}")
    scene.metric("owl load", owl_load["owl"])

    burst_limit = PLAN.requests_per_minute + SECONDS * PLAN.requests_per_minute // 60
    scene.check(
        pigeons_in <= burst_limit,
        f"Gus caps the flock at {pigeons_in} requests: burst plus refill, not one more.",
        f"{pigeons_in} pigeon requests reached the Owl. The gate is wide open.",
    )
    scene.check(
        hedgehog_in == SECONDS,
        "The hedgehog has its own budget and is served every second.",
        f"The hedgehog only got {hedgehog_in}/{SECONDS} answers: the flock ate its budget.",
    )

    giant_prompt = "hiss " * 40_000
    response = gateway.handle(GatewayRequest("python", "owl", giant_prompt))
    scene.check(
        response.status == 429 and "tokens" in response.body,
        "The python's 50k-token prompt is refused on the token budget.",
        f"The python's giant prompt got status {response.status}. Tokens are not limited.",
    )
    small = gateway.handle(GatewayRequest("python", "owl", "One small question"))
    scene.check(
        small.status == 200,
        "The refused giant prompt cost nothing: the python's next small question goes through.",
        "The refused giant prompt still burned the python's budget.",
    )
    scene.check(
        gateway.handle(GatewayRequest(None, "owl", "hi")).status == 401,
        "No API key, no entry.",
        "A request without an API key reached the Owl.",
    )
