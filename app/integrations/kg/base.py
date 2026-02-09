from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class GraphDB(ABC):
    """
    I keep this interface so we can swap KG implementations later if needed.
    """

    @abstractmethod
    def upsert_node(self, node_id: str, label: str, props: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def upsert_edge(self, src_id: str, edge_type: str, dst_id: str, props: dict[str, Any] | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_node(self, node_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def neighbors(self, node_id: str, edge_type: str | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError
