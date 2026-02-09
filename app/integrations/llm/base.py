from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMClient(ABC):
    """
    Interface because tommorow we might have multiple LLM providers.
    """

    @abstractmethod
    def generate_json(self, system_prompt: str, user_prompt: str, timeout_s: int = 30) -> Any:
        raise NotImplementedError
