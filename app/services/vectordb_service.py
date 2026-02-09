from __future__ import annotations

import json
import logging
from typing import Any

from app.integrations.vector.embedder import SentenceTransformerEmbedder
from app.integrations.vector.qdrant_db import QdrantVectorDB
from app.models.memory import Memory
from app.schemas.vectodb import VectorDBUpsertItem

logger = logging.getLogger(__name__)


class VectorDBService:
    """
    I handle vector DB operations for memories.
    """

    def __init__(self) -> None:
        try:
            self.vdb = QdrantVectorDB()
            self.embedder = SentenceTransformerEmbedder()

            logger.debug(
                'Initialized VectorDBService',
                extra={'vdb_dim': getattr(self.vdb, 'dim', None)},
            )
        except Exception:
            logger.exception('Failed to initialize VectorDBService')
            raise

    def _memory_as_text(self, mem: Memory) -> str:
        # Must match your upsert embedding text format.
        return f'{mem.key}\n{json.dumps(mem.value or {}, ensure_ascii=False)}'
    
    def find_duplicate(
        self,
        *,
        key: str | None,
        value: dict,
        min_score: float = 0.95,
    ) -> int | None:
        """
        Returns existing memory_id if duplicate found, else None.
        """
        query = f'{(key or "").strip()}\n{json.dumps(value or {}, ensure_ascii=False)}'
        hits = self.vdb.search(query, limit=1, min_score=min_score)

        if not hits:
            return None

        payload = hits[0].get('payload') or {}
        return payload.get('memory_id')


    def upsert_memory(self, mem: Memory) -> None:
        """
        Upsert DB Memory into VDB (mem.id is the point_id).
        """
        text = f'{mem.key}\n{json.dumps(mem.value or {}, ensure_ascii=False)}'
        vector = self.embedder.embed(text)

        payload = {
            'type': mem.type,
            'scope': mem.scope,
            'key': mem.key,
            'confidence': mem.confidence,
            'value': mem.value or {},
            'source_event_id': mem.event_id,
            'memory_id': int(mem.id),
        }

        self.vdb.upsert(
            point_id=int(mem.id),
            vector=vector,
            payload=payload,
        )


    def _vdb_upsert_memory(self, mem: Memory) -> VectorDBUpsertItem:
        """
        Push memory into Qdrant.
        If a similar memory exists, return its existing memory_id (if present).
        Otherwise, upsert this memory and return it.
        """
        extra_base: dict[str, Any] = {
            'mem_id': getattr(mem, 'id', None),
            'mem_type': getattr(mem, 'type', None),
            'mem_scope': getattr(mem, 'scope', None),
            'mem_key': getattr(mem, 'key', None),
            'source_event_id': getattr(mem, 'source_event_id', None),
        }

        try:
            query = self._memory_as_text(mem)

            # threshold here needs to be strict. ok to have duplicate memoroes in DB but not ok to miss any. 
            hits = self.vdb.search(query, limit=1, min_score=0.95)

            if hits:
                best = hits[0]
                payload = best.get('payload') or {}
                vdb_point_id = best.get('id')
                score = best.get('score')

                existing_memory_id = payload.get('memory_id')

                logger.info(
                    'VDB search hit for memory upsert',
                    extra={
                        **extra_base,
                        'vdb_point_id': vdb_point_id,
                        'vdb_score': score,
                        'existing_memory_id': existing_memory_id,
                        'payload_has_memory_id': 'memory_id' in payload,
                    },
                )

                return VectorDBUpsertItem(existing_memory_id=existing_memory_id, memory_exists=True)

            # No hit => upsert new point.
            vector = self.embedder.embed(query)

            payload = {
                'type': mem.type,
                'scope': mem.scope,
                'key': mem.key,
                'confidence': mem.confidence,
                'value': mem.value or {},
                'source_event_id': mem.source_event_id,
                # Do NOT set 'memory_id' here unless you already have it.
            }

            point_id = int(mem.id)

            self.vdb.upsert(point_id=point_id, vector=vector, payload=payload)

            logger.info(
                'Upserted memory into VDB',
                extra={**extra_base, 'vdb_point_id': point_id},
            )

            return VectorDBUpsertItem(existing_memory_id=None, memory_exists=False)

        except Exception:
            logger.exception(
                'Failed to upsert memory into VDB',
                extra=extra_base,
            )
            raise

    def update_vdb_with_memory_id(self, vdb_id: int, memory_id: int) -> None:
        """
        Update the VDB entry with the corresponding Memory ID after the Memory
        has been stored in the database.
        """
        extra_base = {'vdb_point_id': vdb_id, 'memory_id': memory_id}

        try:
            self.vdb.update_payload_field(
                point_id=vdb_id,
                key='memory_id',
                value=memory_id,
            )

            logger.info(
                'Updated VDB payload with memory_id',
                extra=extra_base,
            )

        except Exception:
            logger.exception(
                'Failed to update VDB payload with memory_id',
                extra=extra_base,
            )
            raise
