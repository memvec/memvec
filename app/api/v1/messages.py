import os
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.message import MessageIn, MessageOut
from app.schemas.event import EventCreate
from app.services.event_service import EventService
from app.services.memory_service import MemoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/messages', tags=['messages'])

event_svc = EventService()
memory_svc = MemoryService()

USER_ACTOR = os.getenv('USER_ACTOR', 'user').strip()
SYS_ACTOR = os.getenv('SYSTEM_ACTOR', 'system').strip()

def _generate_output_prompt(evt, memories) -> str | None:
    if not memories:
        return 'Got it.'

    if len(memories) == 1:
        mem = memories[0]
        return f'Noted: {mem.key}'

    return f'Noted {len(memories)} items.'


@router.post('', response_model=MessageOut)
def handle_message(payload: MessageIn, db: Session = Depends(get_db)) -> MessageOut:
    logger.debug(
        'POST /v1/messages called',
        extra={
            'actor_type': USER_ACTOR,
            'actor_id': payload.actor_id,
            'has_text': bool(payload.text),
        },
    )

    incoming_evt = event_svc.create_event(
        db,
        EventCreate(
            actor_type=USER_ACTOR,
            actor_id=payload.actor_id,
            text=payload.text,
            payload=payload.payload,
        ),
    )

    logger.debug(
        'Incoming event created',
        extra={'event_id': incoming_evt.id},
    )

    memories = memory_svc.process_event_to_memories(db, incoming_evt)

    logger.debug(
        'Processed event to memories',
        extra={
            'event_id': incoming_evt.id,
            'memories_created': len(memories),
        },
    )

    output_text = _generate_output_prompt(incoming_evt, memories)

    if output_text:
        system_evt = event_svc.create_event(
            db,
            EventCreate(
                actor_type=SYS_ACTOR,
                actor_id='memvec',
                text=output_text,
                payload={
                    'in_response_to_event_id': incoming_evt.id,
                },
            ),
        )

        logger.debug(
            'System response event created',
            extra={
                'event_id': system_evt.id,
                'in_response_to_event_id': incoming_evt.id,
            },
        )

    return MessageOut(
        event_id=incoming_evt.id,
        output_text=output_text,
        memories_created=len(memories),
    )
