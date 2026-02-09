from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.event import Event
from app.models.memory import Memory
from app.schemas import event
from app.schemas.llm import MemoryQualification
from app.schemas.memory import MemoryCreate
from app.integrations.llm.ollama_client import OllamaClient, LLMJSONError
from app.integrations.llm.prompt import MEMORY_QUALIFIER_SYSTEM, build_memory_qualifier_user_prompt
from app.schemas.vectodb import VectorDBUpsertItem
from app.services.kg_service import KGService
from app.services.vectordb_service import VectorDBService

logger = logging.getLogger(__name__)


class MemoryService:
    """
    I keep memory writes here. Processing logic lives here too.
    """

    def __init__(self) -> None:
        self.llm = OllamaClient()
        self.vector_db_svc = VectorDBService()
        self.vector_upsert_item = VectorDBUpsertItem()

        logger.debug('Ollama client to qualify memories from incoming event')

    def _store_memory_in_db(self, db: Session, event: Event, m_type, m_scope, key, m, qual) -> Memory:
        mem = Memory(
                type=m_type,
                scope=m_scope,
                key=key,
                value=m.value or {},
                confidence=float(m.confidence or 0.0),
                event=event,
            )
            
        event.memories.append(mem)

        try:
            db.add(mem)
            db.commit()
            db.refresh(mem)
        except Exception:
            logger.exception(
                'Failed to store qualified memory',
                extra={
                    'event_id': getattr(event, 'id', None),
                    'type': qual.type,
                    'scope': mem.scope,
                    'key': qual.key,
                },
            )
            raise

        logger.debug(
            'Stored qualified memory',
            extra={
                'event_id': getattr(event, 'id', None),
                'memory_id': getattr(mem, 'id', None),
                'type': mem.type,
                'scope': mem.scope,
                'key': mem.key,
            },
        )
        return mem
    

    def _update_memory_assertion_count(self, db: Session, memory_id: int) -> None:
        try:
            mem = db.query(Memory).filter(Memory.id == memory_id).one()
            mem.assertion_count += 1
            db.commit()
            db.refresh(mem)
        except Exception:
            db.rollback()
            logger.exception(
                'Failed to update assertion count for memory',
                extra={'memory_id': memory_id},
            )
            raise

        logger.info(
            'Assertion count incremented',
            extra={
                'memory_id': memory_id,
                'new_assertion_count': mem.assertion_count,
                'key': mem.key,
                'type': mem.type,
                'scope': mem.scope,
            },
        )



    def list_memories(self, db: Session, scope: str | None = None, type: str | None = None) -> list[Memory]:
        """
        Utility method to list memories with optional filtering. Useful for debugging and inspection.
        """

        logger.debug(
            'Listing memories',
            extra={
                'scope': scope,
                'type': type,
            },
        )

        try:
            q = db.query(Memory)
            if scope:
                q = q.filter(Memory.scope == scope)
            if type:
                q = q.filter(Memory.type == type)
            items = q.order_by(Memory.id.desc()).all()
        except Exception:
            logger.exception('Failed to list memories from DB')
            raise

        logger.debug('Listed memories', extra={'count': len(items)})
        return items

    def process_event_to_memories(self, db: Session, event: Event) -> list[Memory]:
        """
        Flow:
        - If LLM is enabled: qualify + store if is_memory=true
        - If LLM is disabled: fall back to a simple 'episode' session memory

        Rules:
        - episode scope is always forced to session
        """
        logger.debug(
            'Processing event to memories',
            extra={
                'event_id': getattr(event, 'id', None),
                'actor_type': getattr(event, 'actor_type', None),
                'actor_id': getattr(event, 'actor_id', None),
                'has_text': bool(getattr(event, 'text', None)),
                'has_payload': bool(getattr(event, 'payload', None)),
                'use_llm_qualifier': settings.use_llm_qualifier,
            },
        )

        if not event.text and not event.payload:
            logger.debug(
                'Event has no text and no payload; skipping',
                extra={'event_id': getattr(event, 'id', None)},
            )
            return []

        # Fallback path (keeps system usable even when LLM is off)
        if not settings.use_llm_qualifier:
            logger.debug(
                'LLM qualifier disabled; using fallback episode memory',
                extra={'event_id': getattr(event, 'id', None)},
            )

            mem = self._store_memory_in_db(db, event,
                type='episode',
                scope='session',
                key='event_summary',
                value={'text': event.text, 'payload': event.payload or {}},
                confidence=0.3,
                source_event_id=event.id,
            )
            return [mem]

        user_prompt = build_memory_qualifier_user_prompt(
            actor_type=event.actor_type,
            actor_id=event.actor_id,
            text=event.text,
            payload=event.payload or {},
        )

        logger.debug(
            'Built memory qualifier user prompt',
            extra={
                'event_id': getattr(event, 'id', None),
                'prompt_preview': user_prompt[:500],
            },
        )

        try:
            raw = self.llm.generate_json(MEMORY_QUALIFIER_SYSTEM, user_prompt, timeout_s=30)
            qual = MemoryQualification.model_validate(raw)
        except LLMJSONError:
            logger.exception(
                'LLM returned non-JSON / unusable JSON for memory qualification',
                extra={'event_id': getattr(event, 'id', None)},
            )
            return []
        except Exception:
            logger.exception(
                'Memory qualification failed (LLM call or validation error)',
                extra={'event_id': getattr(event, 'id', None)},
            )
            return []

        logger.debug(
            'Memory qualification result',
            extra={
                'event_id': getattr(event, 'id', None),
                'is_memory': getattr(qual, 'is_memory', None),
                'type': getattr(qual, 'type', None),
                'scope': getattr(qual, 'scope', None),
                'key': getattr(qual, 'key', None),
                'confidence': getattr(qual, 'confidence', None),
            },
        )

        if len(qual.memories) == 0:
            logger.debug('Qualification says not a memory; skipping', extra={'event_id': getattr(event, 'id', None)})
            return []
        

        logger.debug('Event is qualified as memory', extra={'event_id': getattr(event, 'id', None)})
        memories: list[Memory] = []
        for m in qual.memories:
            # send memory to vectordb and if its not duplicate only then save. 
            existing_memory_id = self.vector_db_svc.find_duplicate(
                key=m.key,
                value=m.value or {},
                min_score=0.95,
            )

            if existing_memory_id:
                logger.info(
                    'Memory already exists. Update assertion count',
                    extra={'memory_id': existing_memory_id},
                )
                self._update_memory_assertion_count(db, existing_memory_id)
                continue

            # if self.vector_upsert_item.memory_exists:
            #     logger.info(
            #         'Memory already exists. Update assertion count for the memory in DB',
            #         extra={'memory_id': self.vector_upsert_item.existing_memory_id},
            #     )
            #     self._update_memory_assertion_count(db, self.vector_upsert_item.existing_memory_id)
            #     continue  # skip storing this memory since it's a duplicate in VDB

            # since there is no exisitng memory in VDB, we can go ahead and store this memory in DB and update 
            # VDB with memory_id after storing in DB.
            m_type = m.type
            m_scope = m.scope or 'profile'
            if m_type == 'episode':
                m_scope = 'session'

            key = (m.key or '').strip()
            if not key:
                key = f'{m_type}_auto'

            mem = self._store_memory_in_db(db, event, m_type, m_scope, key, m, qual)
            memories.append(mem)
            try:
                self.vector_db_svc.upsert_memory(mem)
                logger.debug('Upserted memory to vector DB')
            except Exception:
                logger.exception(
                    'Failed to upsert memory to vector DB',
                    extra={'memory_id': getattr(mem, 'id', None)},
                )
                # for now not sur if i should stop the flow here or be ok with memory not being in VDB. 
                # TODO: revisit later
                pass
        return memories