"""Adoption office: kittens find a family."""

from __future__ import annotations

import logging
from dataclasses import replace

from zoo_platform.domain.errors import Conflict
from zoo_platform.domain.models import Kitten, Principal
from zoo_platform.infrastructure.repositories import KittenRepository

logger = logging.getLogger("zoo.adoptions")


class AdoptionService:
    def __init__(self, kittens: KittenRepository) -> None:
        self._kittens = kittens

    def kitten(self, principal: Principal, kitten_id: str) -> Kitten:
        return self._kittens.get(kitten_id)

    def admit(self, principal: Principal, kitten_id: str, name: str) -> Kitten:
        self._kittens.add(principal.tenant, kitten_id, name)
        return self._kittens.get(kitten_id)

    def adopt(self, principal: Principal, kitten_id: str, family: str) -> Kitten:
        kitten = self._kittens.get(kitten_id)
        if kitten.adopted_by is not None:
            raise Conflict(f"{kitten.name} already has a family")
        self._kittens.set_adopter(kitten_id, family)
        logger.info("%s adopted by %s", kitten_id, family)
        return replace(kitten, adopted_by=family)
