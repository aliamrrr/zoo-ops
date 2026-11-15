"""Client side of the hosted language models."""

from __future__ import annotations

from zoo_platform.domain.models import Answer
from zoo_platform.ports import CompletionRequest, LlmTransport


class LlmGateway:
    def __init__(self, primary: LlmTransport, backup: LlmTransport, backup_model: str) -> None:
        self._primary = primary
        self._backup = backup
        self._backup_model = backup_model

    def complete(self, prompt: str, temperature: float, model: str) -> Answer:
        result = self._primary.complete(
            CompletionRequest(model=model, prompt=prompt, temperature=temperature)
        )
        return Answer(text=result.text, model=result.model)
