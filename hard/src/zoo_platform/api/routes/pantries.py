from __future__ import annotations

from fastapi import APIRouter, Depends

from zoo_platform.api.deps import current_principal, get_container
from zoo_platform.api.schemas import PantryResponse, TransferRequest, TransferResponse
from zoo_platform.container import Container
from zoo_platform.domain.models import Principal

router = APIRouter(prefix="/v1/pantries", tags=["pantries"])


@router.get("/{pantry_id}", response_model=PantryResponse)
def pantry(
    pantry_id: str,
    principal: Principal = Depends(current_principal),
    container: Container = Depends(get_container),
) -> PantryResponse:
    found = container.pantries.pantry(principal, pantry_id)
    return PantryResponse(id=found.id, food_kg=found.food_kg)


@router.post("/transfers", response_model=TransferResponse)
def transfer(
    body: TransferRequest,
    principal: Principal = Depends(current_principal),
    container: Container = Depends(get_container),
) -> TransferResponse:
    source, target = container.pantries.transfer(principal, body.source, body.target, body.kg)
    return TransferResponse(
        source=PantryResponse(id=source.id, food_kg=source.food_kg),
        target=PantryResponse(id=target.id, food_kg=target.food_kg),
    )
