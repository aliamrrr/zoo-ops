"""Request and response bodies of the public API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AnswerRequest(BaseModel):
    question: str = Field(min_length=1, max_length=50_000)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)


class AnswerResponse(BaseModel):
    answer: str
    model: str


class FactUpdate(BaseModel):
    text: str = Field(min_length=1, max_length=2_000)


class OrderRequest(BaseModel):
    animal_id: int
    grams: int = Field(gt=0, le=5_000)


class OrderResponse(BaseModel):
    order_id: str
    animal_id: int
    grams: int


class DeliveryItem(BaseModel):
    reference: str = Field(min_length=1, max_length=64)
    animal_id: int
    grams: int = Field(gt=0, le=5_000)


class DeliveryBatch(BaseModel):
    deliveries: list[DeliveryItem] = Field(max_length=500)


class DeliveryReceipt(BaseModel):
    accepted: int


class BellyResponse(BaseModel):
    animal_id: int
    grams: int


class AnimalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    species: str = Field(min_length=1, max_length=40)
    enclosure_id: int


class CatalogItem(BaseModel):
    id: int
    name: str
    species: str
    enclosure: str
    arrived_at: int


class CatalogResponse(BaseModel):
    items: list[CatalogItem]
    next_offset: int | None = None


class KittenCreate(BaseModel):
    id: str = Field(min_length=1, max_length=40, pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=1, max_length=80)


class KittenResponse(BaseModel):
    id: str
    name: str
    adopted_by: str | None


class AdoptionRequest(BaseModel):
    family: str = Field(min_length=1, max_length=80)


class TransferRequest(BaseModel):
    source: str
    target: str
    kg: int = Field(gt=0, le=1_000)


class PantryResponse(BaseModel):
    id: str
    food_kg: int


class TransferResponse(BaseModel):
    source: PantryResponse
    target: PantryResponse


class IncidentRequest(BaseModel):
    kind: Literal["dirty"]


class PenResponse(BaseModel):
    id: str
    dirty: bool
