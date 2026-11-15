from __future__ import annotations

from fastapi import APIRouter, Depends

from zoo_platform.api.deps import current_principal, get_container
from zoo_platform.api.schemas import AdoptionRequest, KittenCreate, KittenResponse
from zoo_platform.container import Container
from zoo_platform.domain.models import Kitten, Principal

router = APIRouter(prefix="/v1/kittens", tags=["adoptions"])


def _response(kitten: Kitten) -> KittenResponse:
    return KittenResponse(id=kitten.id, name=kitten.name, adopted_by=kitten.adopted_by)


@router.post("", response_model=KittenResponse, status_code=201)
def admit(
    body: KittenCreate,
    principal: Principal = Depends(current_principal),
    container: Container = Depends(get_container),
) -> KittenResponse:
    return _response(container.adoptions.admit(principal, body.id, body.name))


@router.get("/{kitten_id}", response_model=KittenResponse)
def kitten(
    kitten_id: str,
    principal: Principal = Depends(current_principal),
    container: Container = Depends(get_container),
) -> KittenResponse:
    return _response(container.adoptions.kitten(principal, kitten_id))


@router.post("/{kitten_id}/adoption", response_model=KittenResponse)
def adopt(
    kitten_id: str,
    body: AdoptionRequest,
    principal: Principal = Depends(current_principal),
    container: Container = Depends(get_container),
) -> KittenResponse:
    return _response(container.adoptions.adopt(principal, kitten_id, body.family))
