"""Composition root: the one place that builds and wires every component."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from typing import TextIO

import fakeredis
from redis import Redis

from zoo_platform.infrastructure.database import Database, sqlite_factory
from zoo_platform.infrastructure.demo import DemoCrew, DemoModel
from zoo_platform.infrastructure.jobs import JobQueue, Worker
from zoo_platform.infrastructure.llm import LlmGateway
from zoo_platform.infrastructure.repositories import (
    AnimalRepository,
    FactRepository,
    KitchenRepository,
    KittenRepository,
    PantryRepository,
    PenRepository,
)
from zoo_platform.infrastructure.telemetry import configure_logging
from zoo_platform.ports import CleaningCrew, Clock, ConnectionFactory, LlmTransport, Sleeper
from zoo_platform.services.adoptions import AdoptionService
from zoo_platform.services.catalog import CatalogService
from zoo_platform.services.kitchen import KitchenService
from zoo_platform.services.owl import OwlService
from zoo_platform.services.pantries import PantryService
from zoo_platform.services.pens import CLEAN_PEN, PenService
from zoo_platform.settings import Settings


@dataclass(slots=True)
class Adapters:
    """Everything that talks to the outside world. Tests replace these with fakes."""

    clock: Clock
    sleep: Sleeper
    redis: Redis
    owl: LlmTransport
    parrot: LlmTransport
    crew: CleaningCrew
    connect: ConnectionFactory
    log_stream: TextIO


def default_adapters(settings: Settings) -> Adapters:
    redis = Redis.from_url(settings.redis_url) if settings.redis_url else fakeredis.FakeRedis()
    return Adapters(
        clock=time.monotonic,
        sleep=time.sleep,
        redis=redis,
        owl=DemoModel(settings.owl_model, latency_s=0.8),
        parrot=DemoModel(settings.parrot_model, latency_s=0.2),
        crew=DemoCrew(),
        connect=sqlite_factory(settings.database_path),
        log_stream=sys.stderr,
    )


@dataclass(slots=True)
class Container:
    settings: Settings
    adapters: Adapters
    database: Database
    owl: OwlService
    kitchen: KitchenService
    catalog: CatalogService
    adoptions: AdoptionService
    pantries: PantryService
    pens: PenService
    queue: JobQueue
    worker: Worker


def build_container(settings: Settings, adapters: Adapters) -> Container:
    configure_logging(adapters.log_stream, settings.log_level)
    database = Database(adapters.connect)
    database.migrate()

    animals = AnimalRepository(database)
    gateway = LlmGateway(adapters.owl, adapters.parrot, settings.parrot_model)
    queue = JobQueue()
    pens = PenService(PenRepository(database), queue, adapters.crew)

    return Container(
        settings=settings,
        adapters=adapters,
        database=database,
        owl=OwlService(gateway, FactRepository(database), adapters.clock, settings.owl_model),
        kitchen=KitchenService(KitchenRepository(database), animals, adapters.clock),
        catalog=CatalogService(animals, adapters.clock),
        adoptions=AdoptionService(KittenRepository(database)),
        pantries=PantryService(PantryRepository(database)),
        pens=pens,
        queue=queue,
        worker=Worker(queue, {CLEAN_PEN: pens.clean}),
    )
