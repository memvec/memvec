from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MemoryCreate(BaseModel):
    type: str
    scope: str
    key: str
    value: dict
    confidence: float = 0.0

    # NEW
    decay: float = 0.0
    superseded_by_memory_id: int | None = None


class MemoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    scope: str
    key: str
    value: dict
    confidence: float

    # NEW
    assertion_count: int
    decay: float
    superseded_by_memory_id: int | None = None
    created_at: datetime
    event_id: int
