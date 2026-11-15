"""Ticket 02: the global limit."""

import threading

from zoo_planet.edge.gateway import Gateway, SharedStore
from zoo_planet.sim import SimClock


def fleet(clock: SimClock, skews: tuple[float, ...] = (0.0, 0.0, 0.0)) -> list[Gateway]:
    store = SharedStore(clock)
    return [Gateway(f"region-{i}", store, clock.skewed(skew)) for i, skew in enumerate(skews)]


def hammer(gateways: list[Gateway], caller: str, per_gateway: int) -> int:
    admitted: list[bool] = []
    barrier = threading.Barrier(len(gateways) * 4)

    def worker(gateway: Gateway) -> None:
        barrier.wait()
        for _ in range(per_gateway // 4):
            admitted.append(gateway.admit(caller))

    threads = [threading.Thread(target=worker, args=(g,)) for g in gateways for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(30)
    return sum(admitted)


def test_the_limit_holds_across_regions() -> None:
    assert hammer(fleet(SimClock()), "pigeon-bot", per_gateway=100) == 100


def test_the_limit_holds_when_region_clocks_disagree() -> None:
    assert hammer(fleet(SimClock(), skews=(-20.0, 0.0, 25.0)), "pigeon-bot", per_gateway=100) == 100


def test_there_is_no_double_burst_at_a_minute_boundary() -> None:
    clock = SimClock(start=1_700_000_020.0)
    gateways = fleet(clock)
    clock.advance(19.9)
    first = sum(gateways[i % 3].admit("pigeon-bot") for i in range(100))
    clock.advance(0.2)
    second = sum(gateways[i % 3].admit("pigeon-bot") for i in range(100))
    assert first == 100
    assert second <= 2, "a window reset must not hand out a second full burst"


def test_the_budget_refills_smoothly() -> None:
    clock = SimClock()
    gateways = fleet(clock)
    assert sum(gateways[0].admit("hedgehog") for _ in range(100)) == 100
    clock.advance(30)
    assert sum(gateways[1].admit("hedgehog") for _ in range(100)) == 50


def test_callers_do_not_share_budgets() -> None:
    clock = SimClock()
    gateways = fleet(clock)
    hammer(gateways, "pigeon-bot", per_gateway=100)
    assert gateways[2].admit("hedgehog")
