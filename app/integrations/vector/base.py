from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class VectorDB(ABC):
    """
    I keep this interface so Qdrant can be swapped later without touching services.
    """

    @abstractmethod
    def ensure_ready(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def upsert(self, point_id: str, vector: list[float], payload: dict) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, point_id: str) -> dict | None:
        raise NotImplementedError
