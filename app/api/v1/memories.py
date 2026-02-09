import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.memory import MemoryCreate, MemoryOut
from app.services.memory_service import MemoryService


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/memories', tags=['memories'])

memory_svc = MemoryService()


@router.post('', response_model=MemoryOut)
def create_memory(payload: MemoryCreate, db: Session = Depends(get_db)) -> MemoryOut:
    logger.debug(
        'POST /v1/memories called',
        extra={
            'type': payload.type,
            'scope': payload.scope,
            'key': payload.key,
            'confidence': payload.confidence,
            'source_event_id': payload.source_event_id,
        },
    )

    try:
        mem = memory_svc.create_memory(db, payload)
    except Exception:
        logger.exception(
            'Failed to create memory via API',
            extra={
                'type': payload.type,
                'scope': payload.scope,
                'key': payload.key,
            },
        )
        raise

    logger.debug(
        'POST /v1/memories completed',
        extra={'memory_id': getattr(mem, 'id', None)},
    )
    return mem


@router.get('', response_model=list[MemoryOut])
def list_memories(
    scope: str | None = None,
    type: str | None = None,
    db: Session = Depends(get_db),
) -> list[MemoryOut]:
    logger.debug(
        'GET /v1/memories called',
        extra={
            'scope': scope,
            'type': type,
        },
    )

    try:
        items = memory_svc.list_memories(db, scope=scope, type=type)
    except Exception:
        logger.exception(
            'Failed to list memories via API',
            extra={
                'scope': scope,
                'type': type,
            },
        )
        raise

    logger.debug(
        'GET /v1/memories completed',
        extra={'count': len(items)},
    )
    return items
