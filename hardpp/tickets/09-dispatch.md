# PLANET-209 Dispatching keepers across the city

**Area:** `zoo_planet.dispatch`
**Pattern:** Geospatial index (geohash or grid) with nearest-neighbour search
**Asked at:** Uber (driver dispatch), Lyft, DoorDash, Google Maps

> The Paris network has 20,000 keepers walking between its sites. When a penguin escapes,
> we need the 5 closest available keepers in a few milliseconds. Today every query
> computes the distance to all 20,000.

## Requirements

1. `nearest(lat, lon, k, radius_km)` returns exactly what a brute force would: the `k` closest keepers within `radius_km`, closest first, ties broken by id. Keepers just across a cell border count.
2. With 20,000 keepers in Paris, a query computes **at most 300 distances** on average (`distance_computations`).
3. `update` moves a keeper (they are found at their new position only) and `remove` takes them off duty.

## Constraints

- Any spatial index works: geohash, uniform grid, quadtree, S2 cells. Distances stay haversine.

## Done when

`python -m zoo test --mode hardpp 9` is green.

## Read before you start

- [H3: Uber's hexagonal hierarchical spatial index](https://www.uber.com/blog/h3/)
- [Geohash, Wikipedia](https://en.wikipedia.org/wiki/Geohash)
