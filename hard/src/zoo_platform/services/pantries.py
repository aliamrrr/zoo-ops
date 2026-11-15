"""Food stock: keepers move food between pantries."""

from __future__ import annotations

from zoo_platform.domain.errors import Conflict
from zoo_platform.domain.models import Pantry, Principal
from zoo_platform.infrastructure.repositories import PantryRepository


class PantryService:
    def __init__(self, pantries: PantryRepository) -> None:
        self._pantries = pantries

    def pantry(self, principal: Principal, pantry_id: str) -> Pantry:
        return self._pantries.get(pantry_id)

    def transfer(
        self, principal: Principal, source: str, target: str, kg: int
    ) -> tuple[Pantry, Pantry]:
        origin = self._pantries.get(source)
        if origin.food_kg < kg:
            raise Conflict(f"pantry {source} only has {origin.food_kg} kg")
        self._pantries.set_food(source, origin.food_kg - kg)
        destination = self._pantries.get(target)
        self._pantries.set_food(target, destination.food_kg + kg)
        return self._pantries.get(source), self._pantries.get(target)
