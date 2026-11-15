"""The Owl kiosk: answers visitor questions with a language model and the zoo's facts."""

from __future__ import annotations

import logging

from zoo_platform.domain.models import Answer, Principal
from zoo_platform.infrastructure.llm import LlmGateway
from zoo_platform.infrastructure.repositories import FactRepository
from zoo_platform.ports import Clock

logger = logging.getLogger("zoo.owl")

TOPICS = ("otter", "lion", "penguin", "cat", "fox", "mole", "ant", "canary")
DEFAULT_FACT = "The Owl is still learning about this one."


def topic_of(question: str) -> str:
    lowered = question.lower()
    return next((topic for topic in TOPICS if topic in lowered), "general")


def build_prompt(question: str, fact: str) -> str:
    return (
        f"You are the zoo's Owl. Answer kindly in two sentences.\nFact: {fact}\nVisitor: {question}"
    )


class OwlService:
    def __init__(
        self, gateway: LlmGateway, facts: FactRepository, clock: Clock, model: str
    ) -> None:
        self._gateway = gateway
        self._facts = facts
        self._clock = clock
        self._model = model

    def answer(self, question: str, temperature: float, principal: Principal) -> Answer:
        topic = topic_of(question)
        fact = self._facts.get(topic) or DEFAULT_FACT
        logger.info("answering a %s question for %s", topic, principal.subject)
        return self._gateway.complete(build_prompt(question, fact), temperature, self._model)

    def update_fact(self, topic: str, text: str) -> None:
        self._facts.upsert(topic, text, int(self._clock()))
        logger.info("fact about %s updated", topic)
