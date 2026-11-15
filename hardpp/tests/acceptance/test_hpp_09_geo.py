"""Ticket 09: dispatching keepers across the city."""

import random

from zoo_planet.dispatch.locator import KeeperLocator, haversine_km

PARIS = (48.80, 48.92, 2.25, 2.42)


def city(
    count: int = 20_000, seed: int = 9
) -> tuple[KeeperLocator, dict[str, tuple[float, float]]]:
    rng = random.Random(seed)
    locator = KeeperLocator()
    positions = {}
    for i in range(count):
        lat, lon = rng.uniform(PARIS[0], PARIS[1]), rng.uniform(PARIS[2], PARIS[3])
        positions[f"keeper-{i}"] = (lat, lon)
        locator.update(f"keeper-{i}", lat, lon)
    return locator, positions


def brute_force(
    positions: dict[str, tuple[float, float]], lat: float, lon: float, k: int, radius_km: float
) -> list[str]:
    scored = sorted((haversine_km(lat, lon, *where), keeper) for keeper, where in positions.items())
    return [keeper for d, keeper in scored if d <= radius_km][:k]


def test_nearest_keepers_are_exact() -> None:
    locator, positions = city(5_000)
    rng = random.Random(3)
    for _ in range(150):
        lat, lon = rng.uniform(PARIS[0], PARIS[1]), rng.uniform(PARIS[2], PARIS[3])
        found = [keeper for keeper, _ in locator.nearest(lat, lon, k=5, radius_km=2.0)]
        assert found == brute_force(positions, lat, lon, 5, 2.0)


def test_a_query_looks_at_few_keepers() -> None:
    locator, _ = city()
    rng = random.Random(4)
    locator.distance_computations = 0
    for _ in range(50):
        locator.nearest(rng.uniform(48.82, 48.90), rng.uniform(2.28, 2.40), k=5, radius_km=2.0)
    assert locator.distance_computations / 50 <= 300


def test_keepers_who_move_are_found_where_they_are() -> None:
    locator, positions = city(2_000)
    locator.update("keeper-7", 48.8584, 2.2945)
    positions["keeper-7"] = (48.8584, 2.2945)
    assert locator.nearest(48.8585, 2.2946, k=1)[0][0] == "keeper-7"
    locator.update("keeper-7", 48.8867, 2.3431)
    assert all(
        keeper != "keeper-7" for keeper, _ in locator.nearest(48.8585, 2.2946, k=5, radius_km=0.5)
    )


def test_keepers_off_duty_disappear() -> None:
    locator, _ = city(500)
    nearest = locator.nearest(48.86, 2.33, k=1, radius_km=5.0)[0][0]
    locator.remove(nearest)
    assert locator.nearest(48.86, 2.33, k=1, radius_km=5.0)[0][0] != nearest


def test_an_empty_neighbourhood_returns_nothing() -> None:
    locator, _ = city(500)
    assert locator.nearest(45.76, 4.83, k=3, radius_km=2.0) == []
