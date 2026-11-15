"""The kitchen: meal orders from keepers and deliveries from the food supplier."""

from __future__ import annotations

import logging

from zoo_platform.domain.models import MealOrder, Principal, SupplierDelivery
from zoo_platform.infrastructure.repositories import AnimalRepository, KitchenRepository
from zoo_platform.ports import Clock

logger = logging.getLogger("zoo.kitchen")


class KitchenService:
    def __init__(self, meals: KitchenRepository, animals: AnimalRepository, clock: Clock) -> None:
        self._meals = meals
        self._animals = animals
        self._clock = clock

    def place_order(self, principal: Principal, animal_id: int, grams: int) -> MealOrder:
        self._animals.get(animal_id)
        meal_id = self._meals.record_meal(animal_id, grams, int(self._clock()))
        logger.info("meal %s served to animal %s", meal_id, animal_id)
        return MealOrder(order_id=f"meal-{meal_id}", animal_id=animal_id, grams=grams)

    def receive_deliveries(self, principal: Principal, deliveries: list[SupplierDelivery]) -> int:
        for delivery in deliveries:
            self._meals.record_meal(
                delivery.animal_id,
                delivery.grams,
                int(self._clock()),
                supplier_ref=delivery.reference,
            )
        return len(deliveries)

    def belly(self, principal: Principal, animal_id: int) -> int:
        self._animals.get(animal_id)
        return self._meals.belly(animal_id)
