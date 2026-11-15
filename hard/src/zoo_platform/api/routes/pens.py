from __future__ import annotations

from fastapi import APIRouter, Depends

from zoo_platform.api.deps import current_principal, get_container
from zoo_platform.api.schemas import IncidentRequest, PenResponse
from zoo_platform.container import Container
from zoo_platform.domain.models import Principal

router = APIRouter(prefix="/v1/pens", tags=["pens"])


@router.get("/{pen_id}", response_model=PenResponse)
def pen(
    pen_id: str,
    principal: Principal = Depends(current_principal),
    container: Container = Depends(get_container),
) -> PenResponse:
    found = container.pens.pen(principal, pen_id)
    return PenResponse(id=found.id, dirty=found.dirty)


@router.post("/{pen_id}/incidents", response_model=PenResponse, status_code=202)
def report(
    pen_id: str,
    body: IncidentRequest,
    principal: Principal = Depends(current_principal),
    container: Container = Depends(get_container),
) -> PenResponse:
    found = container.pens.report_dirty(principal, pen_id)
    return PenResponse(id=found.id, dirty=found.dirty)
