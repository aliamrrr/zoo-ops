"""Pens: incidents reported by keepers, cleaned by the robot crew in the background."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from zoo_platform.domain.models import Job, Pen, Principal
from zoo_platform.infrastructure.jobs import JobQueue
from zoo_platform.infrastructure.repositories import PenRepository
from zoo_platform.ports import CleaningCrew

logger = logging.getLogger("zoo.pens")

CLEAN_PEN = "clean_pen"


class PenService:
    def __init__(self, pens: PenRepository, queue: JobQueue, crew: CleaningCrew) -> None:
        self._pens = pens
        self._queue = queue
        self._crew = crew

    def pen(self, principal: Principal, pen_id: str) -> Pen:
        return self._pens.get(pen_id)

    def report_dirty(self, principal: Principal, pen_id: str) -> Pen:
        self._pens.get(pen_id)
        self._pens.set_dirty(pen_id, True)
        self._queue.put(Job(id=uuid.uuid4().hex, kind=CLEAN_PEN, payload={"pen_id": pen_id}))
        return self._pens.get(pen_id)

    def clean(self, payload: dict[str, Any]) -> None:
        pen_id = str(payload["pen_id"])
        self._crew.dispatch(pen_id)
        self._pens.set_dirty(pen_id, False)
        logger.info("pen %s is clean", pen_id)
