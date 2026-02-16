from pydantic import BaseModel
from typing import Any, Optional


class MessageIn(BaseModel):
    text: Optional[str] = None
    payload: dict[str, Any] | None = None

    actor_type: str = 'user'
    actor_id: str | None = None

    thread_id: str | None = None
    idempotency_key: str | None = None


class MessageOut(BaseModel):
    event_id: int
    output_text: str | None = None

    memories_created: int = 0
