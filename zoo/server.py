"""The game server: serves the page, reports the zoo systems, runs the live kiosk and food bowls.

Every game endpoint takes a `mode` and delegates to that mode's `ModeRuntime`: the routes never
know whether they serve Classic or a hard mode. `create_app` builds an isolated app (tests make
one each); `app` is the one uvicorn serves.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from zoo import owl
from zoo.blueprint import InvalidPlacement
from zoo.checks import ResultsBoard, StatusBoard
from zoo.game import AskOutcome
from zoo.modes import CLASSIC, all_modes, find_mode
from zoo.paths import STATE_DIR
from zoo.runtimes import ClassicRuntime, ModeRuntime, NoBlueprint, build_runtimes

STATIC = Path(__file__).resolve().parent / "static"
REAL_SECONDS_PER_SIM_SECOND = 0.6
MAX_WAIT_SECONDS = 7.0
FIRST_TOKEN_SECONDS = 0.3

router = APIRouter()


class NoCacheStaticFiles(StaticFiles):
    """The page is edited live while you play: browsers must revalidate (ETag), never guess."""

    def file_response(self, *args: Any, **kwargs: Any) -> Any:
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache"
        return response


def current_runtime(
    request: Request, mode: str = Query(CLASSIC, pattern=r"^[a-z+]{2,12}$")
) -> ModeRuntime:
    try:
        key = find_mode(mode).key
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=exc.args[0]) from exc
    runtimes: dict[str, ModeRuntime] = request.app.state.runtimes
    return runtimes[key]


def classic_runtime(request: Request) -> ClassicRuntime:
    runtime = request.app.state.runtimes[CLASSIC]
    assert isinstance(runtime, ClassicRuntime)
    return runtime


Runtime = Annotated[ModeRuntime, Depends(current_runtime)]
Classic = Annotated[ClassicRuntime, Depends(classic_runtime)]


class PlacementIn(BaseModel):
    slot: str | None = Field(default=None, max_length=40)
    links: list[str] = Field(default_factory=list, max_length=12)


class BlueprintIn(BaseModel):
    placements: dict[str, PlacementIn] = Field(max_length=12)


@router.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
def readyz() -> dict[str, str]:
    return {"status": "ready"}


@router.get("/api/modes")
def list_modes() -> list[dict[str, object]]:
    return [mode.to_public_dict() for mode in all_modes().values()]


@router.get("/api/levels")
def list_levels(runtime: Runtime) -> list[dict[str, object]]:
    return runtime.public_levels()


@router.post("/api/levels/{level_id}/play")
def play(level_id: str, classic: Classic) -> dict[str, object]:
    """Classic scene replay. Sync endpoint: FastAPI runs it in a worker thread."""
    try:
        return classic.play(level_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=exc.args[0]) from exc


@router.get("/api/game/systems")
def systems(runtime: Runtime) -> dict[str, dict[str, object]]:
    return runtime.systems()


@router.get("/api/blueprint")
def get_blueprint(runtime: Runtime) -> dict[str, object]:
    try:
        blueprint = runtime.blueprint()
    except NoBlueprint as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"blueprint": blueprint.public(), "progress": blueprint.progress()}


@router.put("/api/blueprint")
def put_blueprint(runtime: Runtime, body: BlueprintIn) -> object:
    try:
        blueprint = runtime.blueprint()
    except NoBlueprint as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    raw = {level: item.model_dump() for level, item in body.placements.items()}
    try:
        return blueprint.save(raw)
    except InvalidPlacement as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/api/game/questions")
def questions() -> dict[str, str]:
    return owl.QUESTIONS


@router.post("/api/game/reset")
async def reset(runtime: Runtime) -> dict[str, str]:
    live = runtime.backend
    await live.run(live.reset)
    return {"status": "reset"}


@router.post("/api/game/feed")
async def feed(
    runtime: Runtime, animal: str = Query(pattern=r"^[a-z]{2,16}$")
) -> dict[str, object]:
    live = runtime.backend
    outcome = await live.run(live.feed, animal)
    await asyncio.sleep(0.25 * outcome.attempts)
    return asdict(outcome)


@router.get("/api/game/ask", response_model=None)
async def ask(
    runtime: Runtime, q: str = Query(min_length=1, max_length=200), storm: bool = False
) -> StreamingResponse | JSONResponse:
    """Streams the answer when async processing is built. Otherwise the visitor waits for the
    whole answer in silence, like a non-streaming API."""
    live = runtime.backend
    outcome: AskOutcome = await live.run(live.ask, q, storm)
    wait = min(outcome.sim_seconds * REAL_SECONDS_PER_SIM_SECOND, MAX_WAIT_SECONDS)
    meta = {key: value for key, value in asdict(outcome).items() if key != "answer"}
    sse_event = runtime.stream_formatter()

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


def create_app(state_dir: Path = STATE_DIR, board: ResultsBoard | None = None) -> FastAPI:
    app = FastAPI(title="Zoo Ops", docs_url="/api/docs", redoc_url=None)
    app.state.runtimes = build_runtimes(board or StatusBoard(state_dir), state_dir)
    app.mount("/static", NoCacheStaticFiles(directory=STATIC), name="static")
    app.include_router(router)
    return app


app = create_app()
