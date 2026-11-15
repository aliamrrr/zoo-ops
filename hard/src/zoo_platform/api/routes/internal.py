"""Operations endpoints. Only reachable from the private network, never through the gateway."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from zoo_platform.api.deps import get_container
from zoo_platform.container import Container

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/worker/drain")
def drain_worker(container: Container = Depends(get_container)) -> dict[str, int]:
    steps = container.worker.drain()
    return {"steps": steps, "pending": len(container.queue)}
