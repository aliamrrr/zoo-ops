"""Keeper dispatch: find the keepers closest to an incident (an escaped penguin, a hurt visitor)."""

from __future__ import annotations

import math

EARTH_RADIUS_KM = 6_371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


class KeeperLocator:
    def __init__(self) -> None:
        self._positions: dict[str, tuple[float, float]] = {}
        self.distance_computations = 0

    def update(self, keeper_id: str, lat: float, lon: float) -> None:
        self._positions[keeper_id] = (lat, lon)

    def remove(self, keeper_id: str) -> None:
        self._positions.pop(keeper_id, None)

    def _distance(self, lat: float, lon: float, keeper_id: str) -> float:
        self.distance_computations += 1
        k_lat, k_lon = self._positions[keeper_id]
        return haversine_km(lat, lon, k_lat, k_lon)

    def nearest(
        self, lat: float, lon: float, k: int = 1, radius_km: float = 2.0
    ) -> list[tuple[str, float]]:
        """The `k` closest keepers within `radius_km`, closest first, ties broken by id."""
        scored = ((self._distance(lat, lon, keeper), keeper) for keeper in self._positions)
        within = sorted((d, keeper) for d, keeper in scored if d <= radius_km)
        return [(keeper, d) for d, keeper in within[:k]]
