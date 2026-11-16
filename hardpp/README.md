# Zoo Planet

Zoo Ops grew into a planet: three regions, a dozen services, millions of visitors. Zoo
Planet is the distributed core behind every site, written as a deterministic simulation so
that crashes, clock skew, network delays and pauses can be replayed exactly in a test.

This is **Zoo Ops [Hard++]**. The ten tickets in [`tickets/`](tickets) are the kind of
problems asked in system design and coding interviews at Google, Amazon, Meta, Uber or
Stripe: cache stampedes, global rate limits, tail latency, exactly-once billing, distributed
tracing, resharding, sagas, partitioned logs, geospatial search and leader election. There are
no TODOs and no hints in the code. Each ticket states a contract; you decide the design.

## Before you code: the blueprint

Each ticket has a block on the planet's architecture blueprint. Open the game in this mode,
go to the **Blueprint** tab, place each block where it belongs and link it to the components
it must talk to. Two places on the diagram are traps. A ticket only ships, in the game, when
its tests pass **and** its block is in the right place.

```bash
./zoo.sh play hardpp        # macOS, Linux, WSL
.\zoo.cmd play hardpp        # Windows
```

## Run the tests

```bash
python -m zoo test --mode hardpp        # every ticket, with a scoreboard
python -m zoo test --mode hardpp 4 -v   # ticket 04, every test listed
cd hardpp && pytest                     # plain pytest
```

The project has no dependencies outside the standard library. Tests drive the simulation
through the public API of each package and inject failures through `zoo_planet.sim`:

- `SimClock` is the only source of time. A skewed clock simulates a region whose clock is off.
- `CrashPlan` arms named crash points. Code calls `crash.point("name")` where a process
  could die, and the test decides when it does.

## Layout

```
src/zoo_planet/
  sim.py            simulated time and crash injection
  cache/            answer cache nodes and the service in front of them
  edge/             regional gateways and the global store they share
  models/           the model replica fleet
  orders/           orders, the message broker and billing
  tracing/          the tracer and the feeding pipeline it instruments
  storage/          the sharded animal registry
  adoption/         the international adoption workflow and its partner services
  stream/           the event log and its consumer groups
  dispatch/         the keeper locator
  coordination/     leases and the nightly scheduler
tests/acceptance/   one file per ticket
tickets/            the ten incidents
architecture/       the blueprint used by the game
```

Some modules are servers you do not own (a shard, a replica, a partner API, the broker).
Tickets say which ones must not change.

## Starting over

```bash
python -m zoo reset --mode hardpp --project
```

This restores `hardpp/src/zoo_planet` to the version you started from (where your branch left
`main`) and discards your changes there.
