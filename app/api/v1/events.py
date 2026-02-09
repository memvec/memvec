import os
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.event import EventCreate, EventOut
from app.schemas.memory import MemoryOut
from app.services.event_service import EventService
from app.services.memory_service import MemoryService


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/events', tags=['events'])

event_svc = EventService()
memory_svc = MemoryService()


@router.post('', response_model=EventOut)
def create_event(payload: EventCreate, db: Session = Depends(get_db)) -> EventOut:
    logger.debug(
        'POST /v1/events called',
        extra={
            'actor_type': payload.actor_type,
            'actor_id': payload.actor_id,
            'has_text': bool(payload.text),
            'has_payload': bool(payload.payload),
        },
    )

    evt = event_svc.create_event(db, payload)

    logger.debug(
        'Event created; processing to memories',
        extra={'event_id': getattr(evt, 'id', None)},
    )

    try:
        memory_svc.process_event_to_memories(db, evt)
    except Exception:
        run_llm_tests = os.getenv('RUN_LLM_TESTS', 'false').lower() in ('1', 'true', 'yes')

        logger.exception(
            'process_event_to_memories failed in create_event',
            extra={
                'event_id': getattr(evt, 'id', None),
                'RUN_LLM_TESTS': run_llm_tests,
            },
        )

        # do NOT hide LLM issues during integration tests.
        if run_llm_tests:
            raise
            
    logger.debug(
        'POST /v1/events completed',
        extra={'event_id': getattr(evt, 'id', None)},
    )
    return evt


@router.get('/{event_id}', response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)) -> EventOut:
    logger.debug(
        'GET /v1/events/{event_id} called',
        extra={'event_id': event_id},
    )

    evt = event_svc.get_event(db, event_id)
    if not evt:
        logger.debug(
            'Event not found',
            extra={'event_id': event_id},
        )
        raise HTTPException(status_code=404, detail='event not found')

    logger.debug(
        'Event fetched',
        extra={'event_id': event_id},
    )
    return evt


@router.post('/{event_id}/process', response_model=list[MemoryOut])
def process_event(event_id: int, db: Session = Depends(get_db)) -> list[MemoryOut]:
    logger.debug(
        'POST /v1/events/{event_id}/process called',
        extra={'event_id': event_id},
    )

    evt = event_svc.get_event(db, event_id)
    if not evt:
        logger.debug(
            'Event not found for processing',
            extra={'event_id': event_id},
        )
        raise HTTPException(status_code=404, detail='event not found')

    try:
        result = memory_svc.process_event_to_memories(db, evt)
    except Exception:
        logger.exception(
            'process_event_to_memories failed in /process endpoint',
            extra={'event_id': event_id},
        )
        raise

    logger.debug(
        'POST /v1/events/{event_id}/process completed',
        extra={
            'event_id': event_id,
            'memories_written': len(result),
        },
    )
    return result
