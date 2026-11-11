"""The game server: serves the page, checks the zoo systems, runs the live kiosk and food bowls."""

from __future__ import annotations

import asyncio
import importlib
import json
from collections.abc import AsyncIterator, Callable
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from zoo import owl
from zoo.game import GameBackend
from zoo.registry import LEVELS, find_level, play_level

STATIC = Path(__file__).resolve().parent / "static"
REAL_SECONDS_PER_SIM_SECOND = 0.6
MAX_WAIT_SECONDS = 7.0
FIRST_TOKEN_SECONDS = 0.3

app = FastAPI(title="Zoo Ops", docs_url="/api/docs", redoc_url=None)
app.mount("/static", StaticFiles(directory=STATIC), name="static")
backend = GameBackend()


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/api/levels")
def list_levels() -> list[dict[str, object]]:
    return [level.to_public_dict() for level in LEVELS]


@app.post("/api/levels/{level_id}/play")
def play(level_id: str) -> dict[str, object]:
    """Sync endpoint: FastAPI runs it in a worker thread, scenes may block for a moment."""
    try:
        level = find_level(level_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    result = play_level(level).to_dict()
    result["todos_left"] = level.todos_left()
    return result


@app.get("/api/game/systems")
def systems() -> dict[str, dict[str, object]]:
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


@app.get("/api/game/questions")
def questions() -> dict[str, str]:
    return owl.QUESTIONS


@app.post("/api/game/reset")
async def reset() -> dict[str, str]:
    await backend.run(backend.reset)
    return {"status": "reset"}


@app.post("/api/game/feed")
async def feed(animal: str = Query(pattern=r"^[a-z]{2,16}$")) -> dict[str, object]:
    outcome = await backend.run(backend.feed, animal)
    await asyncio.sleep(0.25 * outcome.attempts)
    return asdict(outcome)


def load_sse_event() -> Callable[..., str] | None:
    """The learner's sse_event from level 08, or None while it is a TODO or does not load."""
    try:
        sse_event = importlib.import_module("levels.l08_async.async_jobs").sse_event
        sse_event("probe")
    except Exception:  # noqa: BLE001 - NotImplementedError, or a file that does not import
        return None
    return sse_event


@app.get("/api/game/ask", response_model=None)
async def ask(
    q: str = Query(min_length=1, max_length=200), storm: bool = False
) -> StreamingResponse | JSONResponse:
    """Streams the answer through the learner's sse_event() when level 08 is built.
    Otherwise the visitor waits for the whole answer in silence, like a non-streaming API."""
    outcome = await backend.run(backend.ask, q, storm)
    wait = min(outcome.sim_seconds * REAL_SECONDS_PER_SIM_SECOND, MAX_WAIT_SECONDS)
    meta = {key: value for key, value in asdict(outcome).items() if key != "answer"}
    sse_event = load_sse_event()

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
