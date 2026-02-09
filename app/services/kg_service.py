from __future__ import annotations

import logging
from typing import Any

from app.integrations.kg.base import GraphDB
from app.integrations.kg.nebula_graph import NebulaGraphDB
from app.models.event import Event
from app.models.memory import Memory

logger = logging.getLogger(__name__)


class KGService:
    """
    I translate SQL memories into graph nodes/edges.
    """

    def __init__(self, graph: GraphDB | None = None) -> None:
        self.graph = graph or NebulaGraphDB()

    def upsert_memory(self, mem: Memory, event: Event | None = None) -> None:
        mem_vid = f'memory:{mem.id}'
        try:
            logger.debug(
                'KG upsert_memory start',
                extra={
                    'memory_id': getattr(mem, 'id', None),
                    'has_event': event is not None,
                },
            )

            self.graph.upsert_node(
                mem_vid,
                label='Memory',
                props={
                    'memory_id': mem.id,
                    'type': mem.type,
                    'scope': mem.scope,
                    'key': mem.key,
                    'confidence': mem.confidence,
                },
            )
            logger.debug('KG upserted Memory node', extra={'vid': mem_vid, 'label': 'Memory'})

            if event is not None:
                actor_vid = f'actor:{event.actor_type}:{event.actor_id}'
                self.graph.upsert_node(
                    actor_vid,
                    label='Actor',
                    props={'actor_type': event.actor_type, 'actor_id': event.actor_id},
                )
                logger.debug(
                    'KG upserted Actor node')

                self.graph.upsert_edge(actor_vid, 'HAS_MEMORY', mem_vid)
                logger.debug(
                    'KG upserted edge')

            entities = self._extract_entities(mem)
            logger.debug('KG extracted entities')

            for ent in entities:
                ent_name = ent.get('name') or ''
                ent_type = ent.get('entity_type') or 'unknown'
                ent_vid = f'entity:{ent_type}:{str(ent_name).lower()}'

                self.graph.upsert_node(ent_vid, label='Entity', props=ent)
                logger.debug(
                    'KG upserted Entity node')

                self.graph.upsert_edge(mem_vid, 'ABOUT', ent_vid)
                logger.debug(
                    'KG upserted edge')

            logger.info('KG upsert_memory done')

        except Exception:
            logger.exception(
                'KG upsert_memory failed')
            raise

    def _extract_entities(self, mem: Memory) -> list[dict[str, Any]]:
        # I keep it dumb and safe for now. Later we can do LLM-assisted entity linking.
        entities: list[dict[str, Any]] = []

        if mem.type == 'preference':
            entities.append({'name': mem.key, 'entity_type': 'preference_key'})

        text = f'{mem.key} {mem.value}'.lower()
        tech = [
            ('qdrant', 'tool'),
            ('fastapi', 'tool'),
            ('sqlalchemy', 'library'),
            ('ollama', 'runtime'),
            ('qwen', 'llm'),
            ('knowledge graph', 'concept'),
        ]
        for name, etype in tech:
            if name in text:
                entities.append({'name': name, 'entity_type': etype})

        return entities
