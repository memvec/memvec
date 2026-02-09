from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.mysql import JSON as MYSQL_JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.event import Event

class Memory(Base):
    """
    I store durable, processed information here.
    """

    __tablename__ = 'memories'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    type: Mapped[str] = mapped_column(String(32), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[dict] = mapped_column(MYSQL_JSON, nullable=False, default=dict)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    assertion_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    decay: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    superseded_by_memory_id: Mapped[int | None] = mapped_column(
        ForeignKey('memories.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    superseded_by_memory = relationship('Memory', remote_side='Memory.id', uselist=False)

    event_id: Mapped[int] = mapped_column(
        ForeignKey('events.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    event: Mapped['Event'] = relationship('Event', back_populates='memories')

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
   
