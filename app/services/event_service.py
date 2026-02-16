from sqlalchemy.orm import Session
import logging

from app.models.event import Event
from app.schemas.event import EventCreate


logger = logging.getLogger(__name__)


class EventService:

    def create_event(self, db: Session, data: EventCreate) -> Event:
        logger.debug(
            'Creating event',
            extra={
                'actor_type': data.actor_type,
                'actor_id': data.actor_id,
                'has_text': bool(data.text),
                'has_payload': bool(data.payload),
            },
        )

        evt = Event(
            actor_type=data.actor_type,
            actor_id=data.actor_id,
            text=data.text,
            payload=data.payload,
        )

        try:
            db.add(evt)
            db.commit()
            db.refresh(evt)
        except Exception:
            logger.exception('Failed to create event in DB')
            raise

        logger.debug(
            'Created event',
            extra={
                'event_id': getattr(evt, 'id', None),
                'actor_type': evt.actor_type,
                'actor_id': evt.actor_id,
            },
        )
        return evt

    def get_event(self, db: Session, event_id: int) -> Event | None:
        logger.debug(
            'Fetching event',
            extra={'event_id': event_id},
        )

        try:
            evt = db.query(Event).filter(Event.id == event_id).first()
        except Exception:
            logger.exception(
                'Failed to fetch event from DB',
                extra={'event_id': event_id},
            )
            raise

        logger.debug(
            'Fetched event',
            extra={
                'event_id': event_id,
                'found': evt is not None,
            },
        )
        return evt
