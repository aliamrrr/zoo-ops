"""The game server: serves the page, checks the zoo systems, runs the live kiosk and food bowls.

Every game endpoint takes a `mode`. Classic runs the learner's level files directly. The hard
modes run each ticket's acceptance tests in the background and play what passes them.
"""

from __future__ import annotations

import asyncio
import importlib
import json
from collections.abc import AsyncIterator, Callable
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from zoo import owl
from zoo.blueprint import Blueprint, InvalidPlacement
from zoo.checks import StatusBoard
from zoo.game import AskOutcome, GameBackend, SimulatedBackend
from zoo.modes import Mode, ModeLevel, all_modes, find_mode
from zoo.registry import LEVELS, find_level, play_level

STATIC = Path(__file__).resolve().parent / "static"
REAL_SECONDS_PER_SIM_SECOND = 0.6
MAX_WAIT_SECONDS = 7.0
FIRST_TOKEN_SECONDS = 0.3

app = FastAPI(title="Zoo Ops", docs_url="/api/docs", redoc_url=None)
app.mount("/static", StaticFiles(directory=STATIC), name="static")
backend = GameBackend()
simulated = {key: SimulatedBackend() for key, mode in all_modes().items() if not mode.is_classic}
board = StatusBoard()


def current_mode(mode: str = Query("classic", pattern=r"^[a-z+]{2,12}$")) -> Mode:
    try:
        return find_mode(mode)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=exc.args[0]) from exc


ModeParam = Annotated[Mode, Depends(current_mode)]


def hard_only(mode: Mode) -> None:
    if mode.is_classic:
        raise HTTPException(status_code=404, detail="Classic mode has no blueprint")


class PlacementIn(BaseModel):
    slot: str | None = Field(default=None, max_length=40)
    links: list[str] = Field(default_factory=list, max_length=12)


class BlueprintIn(BaseModel):
    placements: dict[str, PlacementIn] = Field(max_length=12)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/api/modes")
def list_modes() -> list[dict[str, object]]:
    return [mode.to_public_dict() for mode in all_modes().values()]


@app.get("/api/levels")
def list_levels(mode: ModeParam) -> list[dict[str, object]]:
    if mode.is_classic:
        return [level.to_public_dict() for level in LEVELS]
    return [level.to_public_dict(mode.root) for level in mode.levels]


@app.post("/api/levels/{level_id}/play")
def play(level_id: str) -> dict[str, object]:
    """Classic scene replay. Sync endpoint: FastAPI runs it in a worker thread."""
    try:
        level = find_level(level_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=exc.args[0]) from exc
    result = play_level(level).to_dict()
    result["todos_left"] = level.todos_left()
    return result


def classic_systems() -> dict[str, dict[str, object]]:
    """The morning check: every scene runs once, the game adapts to what works."""
    report = {}
    for level in LEVELS:
        result = play_level(level)
        report[level.id] = {
            "status": result.status,
            "headline": result.headline,
            "metrics": result.metrics,
        }
    return report


def hard_level_entry(
    level: ModeLevel, found: dict[str, Any] | None, placed: bool, checking: bool
) -> dict[str, object]:
    """A ticket is in production when its acceptance tests pass and its block sits at the
    right place of the architecture blueprint."""
    if found is None:
        return {
            "status": "checking",
            "headline": "Running the acceptance tests...",
            "metrics": {},
            "checking": True,
            "results": [],
            "placed": placed,
            "tests_pass": False,
        }
    tests_pass = found["status"] == "healthy"
    failing = [item for item in found["results"] if item["outcome"] != "pass"]
    if tests_pass and placed:
        status, headline = "healthy", level.with_
    elif tests_pass:
        status = "todo"
        headline = f"Every test passes. Place block {level.id} on the Blueprint to ship it."
    else:
        status = found["status"]
        headline = f"{failing[0]['name']}: {failing[0]['message']}" if failing else level.without
    return {
        "status": status,
        "headline": headline,
        "metrics": {
            "acceptance tests": f"{found['passed']}/{found['total']}",
            "blueprint": "placed" if placed else "not placed",
        },
        "checking": checking,
        "results": found["results"],
        "placed": placed,
        "tests_pass": tests_pass,
    }


def hard_systems(mode: Mode) -> dict[str, dict[str, object]]:
    snapshot = board.snapshot(mode)
    checking = snapshot["state"] == "checking"
    levels: dict[str, dict[str, Any]] = snapshot["levels"] or {}  # type: ignore[assignment]
    checks: dict[str, dict[str, Any]] = Blueprint(mode).progress()["checks"]  # type: ignore[assignment]
    report = {
        level.id: hard_level_entry(
            level, levels.get(level.id), checks[level.id]["verdict"] == "correct", checking
        )
        for level in mode.levels
    }
    simulated[mode.key].online = frozenset(
        level_id for level_id, item in report.items() if item["status"] == "healthy"
    )
    return report


@app.get("/api/game/systems")
def systems(mode: ModeParam) -> dict[str, dict[str, object]]:
    return classic_systems() if mode.is_classic else hard_systems(mode)


@app.get("/api/blueprint")
def get_blueprint(mode: ModeParam) -> dict[str, object]:
    hard_only(mode)
    blueprint = Blueprint(mode)
    return {"blueprint": blueprint.public(), "progress": blueprint.progress()}


@app.put("/api/blueprint")
def put_blueprint(mode: ModeParam, body: BlueprintIn) -> dict[str, object]:
    hard_only(mode)
    raw = {level: item.model_dump() for level, item in body.placements.items()}
    try:
        return Blueprint(mode).save(raw)
    except InvalidPlacement as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/game/questions")
def questions() -> dict[str, str]:
    return owl.QUESTIONS


def live_backend(mode: Mode) -> GameBackend | SimulatedBackend:
    if mode.is_classic:
        return backend
    hard_systems(mode)
    return simulated[mode.key]


@app.post("/api/game/reset")
async def reset(mode: ModeParam) -> dict[str, str]:
    live = live_backend(mode)
    await live.run(live.reset)
    return {"status": "reset"}


@app.post("/api/game/feed")
async def feed(mode: ModeParam, animal: str = Query(pattern=r"^[a-z]{2,16}$")) -> dict[str, object]:
    live = live_backend(mode)
    outcome = await live.run(live.feed, animal)
    await asyncio.sleep(0.25 * outcome.attempts)
    return asdict(outcome)


def format_sse(data: str, event: str | None = None, event_id: str | None = None) -> str:
    lines = [f"id: {event_id}"] if event_id is not None else []
    if event is not None:
        lines.append(f"event: {event}")
    lines += [f"data: {line}" for line in data.split("\n")]
    return "\n".join(lines) + "\n\n"


def load_sse_event() -> Callable[..., str] | None:
    """The learner's sse_event from level 08, or None while it is a TODO or does not load."""
    try:
        sse_event = importlib.import_module("levels.l08_async.async_jobs").sse_event
        sse_event("probe")
    except Exception:  # noqa: BLE001 - NotImplementedError, or a file that does not import
        return None
    return sse_event


def stream_formatter(mode: Mode) -> Callable[..., str] | None:
    if mode.is_classic:
        return load_sse_event()
    return format_sse if "08" in simulated[mode.key].online else None


@app.get("/api/game/ask", response_model=None)
async def ask(
    mode: ModeParam, q: str = Query(min_length=1, max_length=200), storm: bool = False
) -> StreamingResponse | JSONResponse:
    """Streams the answer when level 08 is built. Otherwise the visitor waits for the whole
    answer in silence, like a non-streaming API."""
    live = live_backend(mode)
    outcome: AskOutcome = await live.run(live.ask, q, storm)
    wait = min(outcome.sim_seconds * REAL_SECONDS_PER_SIM_SECOND, MAX_WAIT_SECONDS)
    meta = {key: value for key, value in asdict(outcome).items() if key != "answer"}
    sse_event = stream_formatter(mode)

    if sse_event is None:
        await asyncio.sleep(wait)
        return JSONResponse({**meta, "answer": outcome.answer, "streamed": False})

    async def stream() -> AsyncIterator[str]:
        try:
            yield sse_event(json.dumps({**meta, "streamed": True}), event="meta")
            if outcome.failed:
                await asyncio.sleep(wait)
                yield sse_event("failed", event="done")
                return
            first = min(wait, FIRST_TOKEN_SECONDS)
            await asyncio.sleep(first)
            tokens = owl.tokens(outcome.answer)
            step = max(0.03, (wait - first) / max(len(tokens), 1))
            for index, token in enumerate(tokens):
                yield sse_event(token, event="token", event_id=str(index))
                await asyncio.sleep(step)
            yield sse_event("ok", event="done")
        except Exception as exc:  # noqa: BLE001 - shown to the player instead of a dead stream
            yield f"event: crash\ndata: {type(exc).__name__}: {exc}\n\n"

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(stream(), media_type="text/event-stream", headers=headers)
