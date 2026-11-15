"""Interfaces of the outside world. Production and tests plug different adapters behind them."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

Clock = Callable[[], float]
Sleeper = Callable[[float], None]
ConnectionFactory = Callable[[], sqlite3.Connection]


@dataclass(frozen=True, slots=True)
class CompletionRequest:
    model: str
    prompt: str
    temperature: float = 0.0
    timeout_s: float | None = None


@dataclass(frozen=True, slots=True)
class CompletionResult:
    text: str
    model: str


class LlmTransport(Protocol):
    """A hosted language model API. Raises ProviderUnavailable or ProviderRejected."""

    def complete(self, request: CompletionRequest) -> CompletionResult: ...


class CleaningCrew(Protocol):
    """The robot crew that physically cleans a pen. Raises CrewBusy when it cannot."""

    def dispatch(self, pen_id: str) -> None: ...
