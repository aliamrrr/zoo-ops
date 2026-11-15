# Zoo Platform

The backend behind the Zoo Ops visitor app: the Owl kiosk (an LLM question service), the
kitchen, the visitor guide, adoptions, pantries and the robot cleaning crew. It is a real
FastAPI service with a layered architecture, a SQL schema with migrations, Redis, background
jobs and JWT authentication.

This is **Zoo Ops [Hard]**. There are no TODOs in the code. Ten tickets in [`tickets/`](tickets)
describe ten production incidents. For each one you read the ticket, design where the fix
belongs, find the place in the code, and make the ticket's acceptance tests pass.

## Before you code: the blueprint

Each ticket has a block on the architecture blueprint. Open the game in this mode, go to the
**Blueprint** tab, place the block where it belongs in the architecture and link it to the
components it talks to. A ticket only ships, in the game, when its tests pass **and** its
block is in the right place.

```bash
python -m zoo play --mode hard
```

## Run the service

From the repository root, with the virtual environment active:

```bash
cd hard
PYTHONPATH=src uvicorn zoo_platform.api.app:create_default_app --factory --reload
```

On Windows PowerShell: `$env:PYTHONPATH="src"` before the `uvicorn` command.

Configuration comes from `ZOO_*` environment variables (see `settings.py`). Without
`ZOO_REDIS_URL` the service uses an in-process Redis, and the demo models answer locally, so
nothing else needs to run.

## Run the tests

```bash
python -m zoo test --mode hard        # every ticket, with a scoreboard
python -m zoo test --mode hard 3 -v   # ticket 03, every test listed
cd hard && pytest                     # plain pytest, for your IDE or debugger
```

`tests/unit` must stay green the whole time. `tests/acceptance` holds one file per ticket.
The acceptance tests talk to the service through HTTP only, with fakes for time, Redis and
the model providers: they check behavior, not how you wrote it.

## Layout

```
src/zoo_platform/
  api/              FastAPI app, routers, schemas, dependencies, middleware, error mapping
  services/         use cases, one module per area of the zoo
  domain/           models and domain errors, no framework code
  infrastructure/   database, repositories, model gateway, jobs, telemetry, demo adapters
  migrations/       numbered SQL (or Python) migrations, applied in order at startup
  container.py      composition root: builds every service from the settings and adapters
  ports.py          the interfaces the services depend on
  settings.py       configuration
tests/
  unit/             fast tests of the building blocks
  acceptance/       one file per ticket
  zp_testkit.py     the test harness: fake clock, model stubs, traced database, helpers
tickets/            the ten incidents
architecture/       the blueprint used by the game
```

Conventions: services never import FastAPI, routers never touch SQL, time and sleep always
come from the injected `Clock` and `Sleeper`, and new tables or indexes arrive through a new
migration file, never by editing an applied one.

## Starting over

```bash
python -m zoo reset --mode hard --project
```

This restores `hard/src/zoo_platform` from the `hard-starter` tag and discards your changes there.
