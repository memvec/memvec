from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EventCreate(BaseModel):
    actor_type: str = 'user'
    actor_id: str = 'unknown'
    text: str = ''
    payload: dict = {}


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_type: str
    actor_id: str
    text: str
    payload: dict

    created_at: datetime
