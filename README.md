<div align="center">

# Zoo Ops

**Learn 10 backend system design patterns by keeping a cute zoo alive.**

You write the missing backend code. The animals show you, live, what your code changes.

[![CI](https://github.com/aliamrrr/zoo-ops/actions/workflows/ci.yml/badge.svg)](https://github.com/aliamrrr/zoo-ops/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-game%20server-009688?logo=fastapi&logoColor=white)
![Levels](https://img.shields.io/badge/levels-10%20%C3%97%203%20modes-7a62d9)
![License](https://img.shields.io/badge/license-MIT-58c96c)

![The zoo with eight systems built](docs/zoo-built.png)

</div>

## What is this?

Zoo Ops is a small browser game with a real Python backend. You run a zoo for a three-minute shift: visitors line up to ask the Owl questions, animals get hungry, pens get dirty, families adopt kittens, and incidents hit (a pigeon swarm, a storm, a raccoon, a bad release).

The zoo runs on **ten backend systems, one per system design pattern**, and each one has a piece of code missing: 20 to 40 lines that you write.

- A pattern you have not built yet has its keeper **asleep** behind caution tape, and the game shows you what that costs.
- A pattern you built **wakes its keeper up**, and you see it act in the world, with a label saying exactly what it just did.

It is made for people preparing system design interviews, juniors who want to feel why these patterns exist, and anyone who learns better by breaking things.

| Nothing built yet | The dock: one badge per pattern |
| --- | --- |
| ![Every keeper asleep](docs/zoo-unbuilt.png) | ![The pattern dock](docs/dock.png) |

## Quick start

You need Python 3.11 or newer. Nothing else: no Redis, no Postgres, no Docker, no API key.

**Windows (PowerShell)**

```powershell
git clone https://github.com/aliamrrr/zoo-ops.git
cd zoo-ops
powershell -ExecutionPolicy Bypass -File install.ps1
.\.venv\Scripts\Activate.ps1
python -m zoo play
```

**macOS or Linux**

```bash
git clone https://github.com/aliamrrr/zoo-ops.git
cd zoo-ops
sh install.sh
source .venv/bin/activate
python -m zoo play
```

The game opens on http://127.0.0.1:8000. Play one shift first, see everything go wrong, then start building.

## Three ways to play

| Mode | Command | What you get |
| --- | --- | --- |
| **Zoo Ops** (Classic) | `python -m zoo play` | Ten guided levels in [`levels/`](levels). Each pattern is one file with TODOs and a docstring spec. |
| **Zoo Ops [Hard]** | `python -m zoo play --mode hard` | A real FastAPI service in [`hard/`](hard), with layers, migrations, Redis, jobs and auth. Ten tickets, no TODOs: you find where the code goes. Same ten patterns, at production depth. |
| **Zoo Ops [Hard++]** | `python -m zoo play --mode hardpp` | A distributed zoo in [`hardpp/`](hardpp), simulated deterministically. Ten interview-grade problems: stampedes, GCRA, hedged requests, outbox, tail sampling, resharding, sagas, partitioned logs, geo search, fencing tokens. |

You can also switch modes on the title screen of the game. Each mode keeps its own progress
and its own day counter, and `python -m zoo modes` lists them.

### Architecture first: the Blueprint

In the two hard modes, the game has a **Blueprint** tab: the architecture of the project,
drawn as boxes and arrows, with empty places. Before writing code for a ticket, you drag its
block (the cache, the limiter, the outbox relay...) to where it belongs and link it to the
components it talks to. The server checks the design and answers with hints, never with the
solution. A ticket ships, and its keeper wakes up in the zoo, only when **its acceptance tests
pass and its block sits in the right place**.

### Hard++, the ten problems

| # | Ticket | Pattern |
| --- | --- | --- |
| 01 | The viral question | Singleflight, stale-while-revalidate, consistent hashing with virtual nodes |
| 02 | One limit for the whole planet | Distributed GCRA over compare-and-set, immune to clock skew |
| 03 | The long tail | Hedged requests, per-replica concurrency limits, priority load shedding |
| 04 | Billed twice, or never | Transactional outbox, relay, idempotent consumer |
| 05 | The trace that stops at the queue | W3C trace context across a queue, tail-based sampling |
| 06 | The registry outgrew its shards | Consistent-hash sharding, online rebalancing, k-way merge pagination |
| 07 | The half-finished adoption | Orchestrated saga with compensations and crash recovery |
| 08 | Events out of order | Keyed partitions, consumer group rebalancing, commit after processing, fencing |
| 09 | Dispatching keepers across the city | Geospatial grid index, exact k-nearest neighbours |
| 10 | Two night watchmen | Leases and fencing tokens |

## How you play

You are **Bao, the panda keeper**. Click a target and Bao walks there to do the job, so the order you click in is your route:

- **Click a visitor** in the line to send their question across the bridge to the Owl. Serve several in a row to build a **combo**. Golden **VIPs** pay triple but hate waiting.
- **Click an animal** to feed it. Once is enough: overfed animals get sick.
- **Click dirt** to clean a pen, and **the pink cottage** when families wait to adopt.
- **A keeper is asleep?** Do its job by hand: click the pigeons to shoo them, click the raccoon to scare it off, run to the kiosk to roll back a bad release. Building the pattern is what stops you running.
- Each shift you survive unlocks the **next day**, with more visitors. Coins, reputation and visitors served make your score, from zero to three stars.

Three things always tell you which pattern is at work:

1. **In the world**: a labelled callout pops where it happens, like `04 IDEMPOTENCY  3 tries, still 1 meal`.
2. **The dock** under the zoo: the badge of that pattern flashes and counts how often it helped or hurt.
3. **The shift journal**: the story of the shift, each line tagged with its pattern. Click a tag to open its station.

## The ten patterns

| # | Pattern | Keeper | Not built, in the game | Built, in the game |
| --- | --- | --- | --- | --- |
| 01 | **Cache** (Redis cache-aside, TTL, LLM and embedding caches) | Hazel the squirrel | Every question is paid again and visitors wait | Repeated questions come from the nut store, instant and free |
| 02 | **Rate limiting + API gateway** (token buckets per key) | Gus the goose | The pigeon swarm jams the kiosk | Gus throttles the pigeons at the gate |
| 03 | **Reliability** (timeouts, retries with jitter, circuit breaker, fallback) | Rusty the fox | In the storm, questions sink and visitors leave | Rusty retries, opens the breaker, the Parrot answers |
| 04 | **Idempotency** (Idempotency-Key, UNIQUE, upserts) | Miso the cat | Network retries feed an animal 2 or 3 times, it gets sick | Each order is served once, retries are ignored |
| 05 | **Observability** (JSON logs, p95, SLO burn-rate alerts) | Mika the meerkat | You fly blind: no bars, no forecast, no pager | Hunger and patience bars, wait p95, incident forecast, pager |
| 06 | **Database performance** (indexes, N+1, cursor pagination, pooling) | Digby the mole | Every action lags by a second | Actions are instant |
| 07 | **Data integrity** (transactions, locks, optimistic locking) | Bea the beaver | Two families leave with the same kitten | One kitten, one family |
| 08 | **Async processing** (queues, workers, DLQ, SSE streaming) | The ant colony | Silent waits, and you clean every pen by hand | The Owl streams word by word, the ants clean in the background |
| 09 | **Auth + security** (JWT, API keys, tenants, secrets) | Rex the dog | The raccoon walks in and steals coins | Rex refuses the forged badge |
| 10 | **Deployment + scaling** (canary, rollback, health checks, graceful shutdown) | Pip the canary | A bad release breaks the kiosk for everyone | The canary catches it and rolls back |

Levels 01, 03, 04 and 08 run **your code on every click**: the kiosk and the kitchen call your functions directly. The other levels change the game through the result of their scene, checked when the shift starts and each time you come back to the page after saving a file.

## The learning loop

Each level lives in its own folder:

```
levels/l04_idempotency/
  README.md             the pattern in a few lines, its bugs and symptoms, where to learn it, hints
  idempotency.py        the file you edit: every TODO raises NotImplementedError
  test_idempotency.py   the contract your code must meet
  scene.py              a small story that runs your code and checks the zoo
```

1. Pick a level and read its `README.md`.
2. Replace each `raise NotImplementedError(...)` with your code. The docstring is the spec.
3. Run `python -m zoo test 4` until the bench is green.
4. Go back to the game: the keeper is awake, and that part of the shift now works.

Work on your own branch so the starter stays untouched:

```bash
git switch -c solved
git diff starter -- levels/l04_idempotency    # what you changed in a level
python -m zoo reset 4                          # start level 04 over
```

## Commands

| Command | What it does |
| --- | --- |
| `python -m zoo play` | Starts the game and opens it in the browser. It reloads when you save a level |
| `python -m zoo test` | Runs every level's tests with a colored scoreboard in the terminal |
| `python -m zoo test 3 7` | Only levels 3 and 7, listing every test |
| `python -m zoo scene 4` | Plays the story of level 04 in the terminal |
| `python -m zoo reset 4` | Restores the level 04 file from the `starter` tag |
| `python -m zoo modes` | Lists the three modes |
| `python -m zoo play --mode hard` | The game in Hard mode (`hardpp` for Hard++) |
| `python -m zoo test --mode hardpp 4 -v` | The acceptance tests of a Hard++ ticket, every test listed |
| `python -m zoo reset --mode hard --project` | Restores the whole Hard project from the `hard-starter` tag |
| `pytest` | Plain pytest works too, for your IDE or debugger |

## How it works

- **No infrastructure needed.** Redis is emulated by `fakeredis`, SQLite stands in for Postgres, the LLMs (the Owl and the Parrot) are fakes with realistic latency and failures, and incidents run on simulated time.
- **Your code is never mocked.** Tests, scenes and the live game all call the same functions you write.
- **A broken level never breaks the game.** A TODO falls back to the naive behavior the pattern exists to prevent, and even a syntax error only takes down its own part of the zoo.

```
levels/        Classic: the ten levels (the code you write)
hard/          Hard: the Zoo Platform service, its tickets, tests and blueprint
hardpp/        Hard++: the Zoo Planet simulation, its tickets, tests and blueprint
zoo/
  game.py      live hooks: Classic runs your level code, the hard modes play what shipped
  server.py    FastAPI: the page, the systems check, the blueprint, the kiosk stream
  modes.py     the three modes and their manifests (zoo-mode.json)
  checks.py    runs a hard mode's acceptance tests in a subprocess, cached by fingerprint
  blueprint.py checks a blueprint design against answers that never leave the server
  static/      the game: world.js draws the zoo, game.js runs the shift, blueprint.js the editor
tests/         tests of the game shell itself
```

In the hard modes the game runs the acceptance tests in the background whenever a file of
the project changes, and caches the results in `.zoo/`.

The level and ticket tests are red on purpose until you solve them, so CI checks linting,
test collection, the game shell's own tests, the unit tests of the Hard service, that the
game boots, and the Docker image.

## Contributing

Ideas, bug reports and pull requests are welcome: a new incident, a new animal, a clearer hint, a translation. Please do not commit level or ticket solutions to `main`, the fun is in writing them.

## Author

Made by **Ali Anass Amradouch**.

- LinkedIn: https://www.linkedin.com/in/ali-anass-amradouch-321567255/
- Portfolio: https://aliamrrr.github.io/alianassamr.github.io/

If Zoo Ops helped you, a star on the repo helps other people find it.

## License

[MIT](LICENSE). The animals and the zoo are original artwork drawn in code.
