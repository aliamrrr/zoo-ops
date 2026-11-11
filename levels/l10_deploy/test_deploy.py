import hashlib
import subprocess
import sys
import threading
import time

import pytest

from levels.l10_deploy.deploy import (
    Lifecycle,
    ReleaseStats,
    ShuttingDown,
    in_canary,
    judge_canary,
)


def test_canary_is_sticky() -> None:
    assert all(in_canary(f"user-{i}", 30) == in_canary(f"user-{i}", 30) for i in range(500))


def test_canary_is_stable_across_processes() -> None:
    code = (
        "from levels.l10_deploy.deploy import in_canary; "
        "print(''.join('1' if in_canary(f'user-{i}', 50) else '0' for i in range(64)))"
    )
    other = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    ).stdout.strip()
    here = "".join("1" if in_canary(f"user-{i}", 50) else "0" for i in range(64))
    assert other == here, "Python's hash() is salted per process: use sha256"


def test_canary_uses_the_documented_bucket() -> None:
    digest = hashlib.sha256(b"user-42").digest()
    bucket = int.from_bytes(digest[:8], "big") % 100
    assert in_canary("user-42", bucket + 1) is True
    assert in_canary("user-42", bucket) is False


def test_canary_share_matches_the_percent() -> None:
    share = sum(in_canary(f"user-{i}", 10) for i in range(20_000)) / 20_000
    assert 0.09 < share < 0.11


def test_canary_edges() -> None:
    users = [f"user-{i}" for i in range(1_000)]
    assert not any(in_canary(user, 0) for user in users)
    assert all(in_canary(user, 100) for user in users)


BASELINE = ReleaseStats(requests=10_000, errors=50, p95_ms=200)


@pytest.mark.parametrize(
    ("canary", "verdict"),
    [
        (ReleaseStats(requests=50, errors=40, p95_ms=900), "wait"),
        (ReleaseStats(requests=1_000, errors=100, p95_ms=200), "rollback"),
        (ReleaseStats(requests=1_000, errors=5, p95_ms=400), "rollback"),
        (ReleaseStats(requests=1_000, errors=10, p95_ms=240), "promote"),
        (ReleaseStats(requests=1_000, errors=14, p95_ms=250), "promote"),
    ],
)
def test_judge_canary(canary: ReleaseStats, verdict: str) -> None:
    assert judge_canary(BASELINE, canary) == verdict


def test_ready_until_shutdown() -> None:
    lifecycle = Lifecycle()
    assert lifecycle.ready() and lifecycle.live()
    lifecycle.begin_shutdown()
    assert not lifecycle.ready()
    assert lifecycle.live(), "a draining instance is still alive, do not restart it"


def test_track_request_counts_in_flight() -> None:
    lifecycle = Lifecycle()
    with lifecycle.track_request():
        with lifecycle.track_request():
            assert lifecycle.in_flight == 2
        assert lifecycle.in_flight == 1
    assert lifecycle.in_flight == 0


def test_track_request_uncounts_on_error() -> None:
    lifecycle = Lifecycle()
    with pytest.raises(ValueError), lifecycle.track_request():
        raise ValueError("handler crashed")
    assert lifecycle.in_flight == 0


def test_new_requests_are_refused_while_draining() -> None:
    lifecycle = Lifecycle()
    lifecycle.begin_shutdown()
    with pytest.raises(ShuttingDown), lifecycle.track_request():
        pass
    assert lifecycle.in_flight == 0


def test_drain_waits_for_in_flight_requests() -> None:
    lifecycle = Lifecycle()
    started = threading.Event()
    finished: list[str] = []

    def slow_request() -> None:
        with lifecycle.track_request():
            started.set()
            time.sleep(0.15)
            finished.append("done")

    thread = threading.Thread(target=slow_request)
    thread.start()
    started.wait(1)
    lifecycle.begin_shutdown()
    assert lifecycle.wait_until_drained(timeout=2) is True
    assert finished == ["done"], "drained must mean the request completed"
    thread.join()


def test_drain_times_out() -> None:
    lifecycle = Lifecycle()
    with lifecycle.track_request():
        lifecycle.begin_shutdown()
        began = time.monotonic()
        assert lifecycle.wait_until_drained(timeout=0.1) is False
        assert time.monotonic() - began < 1
