"""The visitor guide: browse animals by species."""

from __future__ import annotations

from zoo_platform.domain.models import CatalogEntry, CatalogPage, Principal
from zoo_platform.infrastructure.repositories import AnimalRepository
from zoo_platform.ports import Clock


class CatalogService:
    def __init__(self, animals: AnimalRepository, clock: Clock) -> None:
        self._animals = animals
        self._clock = clock

    def page(self, principal: Principal, species: str, offset: int, limit: int) -> CatalogPage:
        animals = self._animals.list_by_species(species, offset, limit + 1)
        items = [
            CatalogEntry(
                animal.id,
                animal.name,
                animal.species,
                self._animals.enclosure_name(animal.enclosure_id),
                animal.arrived_at,
            )
            for animal in animals[:limit]
        ]
        return CatalogPage(items, offset + limit if len(animals) > limit else None)

    def register(self, principal: Principal, name: str, species: str, enclosure_id: int) -> int:
        return self._animals.add(principal.tenant, name, species, enclosure_id, int(self._clock()))
