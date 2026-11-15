from __future__ import annotations

from fastapi import APIRouter, Depends

from zoo_platform.api.deps import current_principal, get_container
from zoo_platform.api.schemas import (
    BellyResponse,
    DeliveryBatch,
    DeliveryReceipt,
    OrderRequest,
    OrderResponse,
)
from zoo_platform.container import Container
from zoo_platform.domain.models import Principal, SupplierDelivery

router = APIRouter(tags=["kitchen"])


@router.post("/v1/kitchen/orders", response_model=OrderResponse, status_code=201)
def place_order(
    body: OrderRequest,
    principal: Principal = Depends(current_principal),
    container: Container = Depends(get_container),
) -> OrderResponse:
    order = container.kitchen.place_order(principal, body.animal_id, body.grams)
    return OrderResponse(order_id=order.order_id, animal_id=order.animal_id, grams=order.grams)


@router.post("/v1/kitchen/supplier-deliveries", response_model=DeliveryReceipt)
def receive_deliveries(
    body: DeliveryBatch,
    principal: Principal = Depends(current_principal),
    container: Container = Depends(get_container),
) -> DeliveryReceipt:
    deliveries = [
        SupplierDelivery(item.reference, item.animal_id, item.grams) for item in body.deliveries
    ]
    return DeliveryReceipt(accepted=container.kitchen.receive_deliveries(principal, deliveries))


@router.get("/v1/animals/{animal_id}/belly", response_model=BellyResponse)
def belly(
    animal_id: int,
    principal: Principal = Depends(current_principal),
    container: Container = Depends(get_container),
) -> BellyResponse:
    return BellyResponse(animal_id=animal_id, grams=container.kitchen.belly(principal, animal_id))
