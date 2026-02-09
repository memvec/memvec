from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from app.core.config import settings
from app.integrations.vector.base import VectorDB
from app.integrations.vector.embedder import SentenceTransformerEmbedder


class QdrantVectorDB(VectorDB):
    """
    I keep Qdrant operations here: ensure collection + upsert + get + search.
    """

    def __init__(self) -> None:
        self.client = QdrantClient(url=settings.qdrant_url)
        self.collection = settings.qdrant_collection
        self.embedder = SentenceTransformerEmbedder()
        self.dim = self.embedder.dim

    def ensure_ready(self) -> None:
        existing = {c.name for c in self.client.get_collections().collections}
        if self.collection in existing:
            return

        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=qm.VectorParams(
                size=self.dim,
                distance=qm.Distance.COSINE,
            ),
        )

    def upsert(self, point_id: int, vector: list[float], payload: dict) -> None:
        self.ensure_ready()
        self.client.upsert(
            collection_name=self.collection,
            points=[
                qm.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )

    def get(self, point_id: str) -> dict | None:
        self.ensure_ready()
        points = self.client.retrieve(
            collection_name=self.collection,
            ids=[point_id],
        )
        if not points:
            return None

        p = points[0]
        return {
            'id': str(p.id),
            'payload': p.payload or {},
        }

    def search(
        self,
        query: str,
        *,
        limit: int = 3,
        min_score: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Pure semantic search.
        """

        self.ensure_ready()

        query_vector = self.embedder.embed(query)

        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=limit,
        )

        hits: list[dict[str, Any]] = []

        for r in results:
            if min_score is not None and r.score < min_score:
                continue

            hits.append(
                {
                    'id': str(r.id),
                    'score': r.score,
                    'payload': r.payload or {},
                }
            )

        return hits
    
    def update_payload_field(
        self,
        point_id: str,
        key: str,
        value: object,
    ) -> None:
        """
        Update a single payload field for an existing point.
        """
        self.ensure_ready()

        self.client.set_payload(
            collection_name=self.collection,
            payload={key: value},
            points=[point_id],
        )
