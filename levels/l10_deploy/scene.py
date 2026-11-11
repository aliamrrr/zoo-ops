"""Scene 10: Pip the canary sings every new song version first."""

from __future__ import annotations

import random
import threading
import time

from levels.l10_deploy.deploy import (
    Lifecycle,
    ReleaseStats,
    ShuttingDown,
    in_canary,
    judge_canary,
)
from zoo.kit import Scene

USERS = [f"visitor-{i}" for i in range(4_000)]


def simulate(
    version_error_rate: float, version_p95: float, percent: float, seed: int
) -> tuple[ReleaseStats, ReleaseStats]:
    rng = random.Random(seed)
    counts = {"baseline": [0, 0], "canary": [0, 0]}
    for user in USERS:
        side = "canary" if in_canary(user, percent) else "baseline"
        rate = version_error_rate if side == "canary" else 0.004
        counts[side][0] += 1
        counts[side][1] += rng.random() < rate
    baseline = ReleaseStats(counts["baseline"][0], counts["baseline"][1], 180)
    canary = ReleaseStats(counts["canary"][0], counts["canary"][1], version_p95)
    return baseline, canary


def play(scene: Scene) -> None:
    sticky = all(in_canary(user, 10) == in_canary(user, 10) for user in USERS[:200])
    share = sum(in_canary(user, 10) for user in USERS) / len(USERS)
    scene.metric("canary share", f"{share:.1%}")
    scene.check(
        sticky and 0.08 < share < 0.12,
        f"10% of visitors hear the new song, always the same ones ({share:.1%}).",
        f"Canary routing is off: share {share:.1%}, sticky={sticky}.",
    )

    baseline, canary = simulate(version_error_rate=0.12, version_p95=190, percent=10, seed=1)
    verdict = judge_canary(baseline, canary)
    scene.metric("song v2", verdict)
    scene.check(
        verdict == "rollback",
        f"Song v2 breaks {canary.error_rate:.0%} of requests on the canary: rolled back "
        "before the whole flock heard it.",
        f"Song v2 fails {canary.error_rate:.0%} of canary requests and the verdict "
        f"was '{verdict}'.",
    )

    baseline, canary = simulate(version_error_rate=0.004, version_p95=185, percent=10, seed=2)
    verdict = judge_canary(baseline, canary)
    scene.metric("song v3", verdict)
    scene.check(
        verdict == "promote",
        "Song v3 matches the baseline: promoted to the whole flock.",
        f"Song v3 is healthy but the verdict was '{verdict}'.",
    )

    lifecycle = Lifecycle()
    lifecycle.ready()
    with lifecycle.track_request():
        pass
    started = threading.Barrier(6)
    completed: list[int] = []

    def request(n: int) -> None:
        with lifecycle.track_request():
            started.wait(2)
            time.sleep(0.05 + 0.02 * n)
            completed.append(n)

    threads = [threading.Thread(target=request, args=(n,)) for n in range(5)]
    for thread in threads:
        thread.start()
    started.wait(2)
    lifecycle.begin_shutdown()
    try:
        with lifecycle.track_request():
            late = "served"
    except ShuttingDown:
        late = "refused"
    drained = lifecycle.wait_until_drained(timeout=3)
    for thread in threads:
        thread.join(3)

    scene.info("SIGTERM arrives while 5 visitors are mid-song.")
    scene.metric("dropped requests", 5 - len(completed))
    scene.check(
        not lifecycle.ready(),
        "Readiness turns red: the load balancer stops sending.",
        "Still 'ready' after SIGTERM: new traffic keeps coming during shutdown.",
    )
    scene.check(
        late == "refused",
        "A late visitor gets a 503 and is retried on another pod.",
        "A request was accepted after shutdown began.",
    )
    scene.check(
        drained and len(completed) == 5,
        "All 5 in-flight songs finished before the process exited.",
        f"Shutdown cut {5 - len(completed)} songs in the middle.",
    )
