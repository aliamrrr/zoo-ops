from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from zoo_platform.api.deps import current_principal, get_container
from zoo_platform.api.schemas import AnimalCreate, CatalogItem, CatalogResponse
from zoo_platform.container import Container
from zoo_platform.domain.models import Principal

router = APIRouter(prefix="/v1/animals", tags=["catalog"])


@router.get("", response_model=CatalogResponse)
def browse(
    species: str = Query(min_length=1, max_length=40),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(current_principal),
    container: Container = Depends(get_container),
) -> CatalogResponse:
    page = container.catalog.page(principal, species, offset, limit)
    items = [
        CatalogItem(
            id=e.id, name=e.name, species=e.species, enclosure=e.enclosure, arrived_at=e.arrived_at
        )
        for e in page.items
    ]
    return CatalogResponse(items=items, next_offset=page.next_offset)


@router.post("", status_code=201)
def register(
    body: AnimalCreate,
    principal: Principal = Depends(current_principal),
    container: Container = Depends(get_container),
) -> dict[str, int]:
    return {"id": container.catalog.register(principal, body.name, body.species, body.enclosure_id)}
