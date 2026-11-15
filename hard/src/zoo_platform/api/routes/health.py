from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
def readiness() -> dict[str, str]:
    return {"status": "ready"}
