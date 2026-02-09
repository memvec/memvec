from __future__ import annotations
from typing import TYPE_CHECKING


from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.mysql import JSON as MYSQL_JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.memory import Memory

class Event(Base):
    """
    Store=ing the raw incoming message here. along with its memories. 
    """

    __tablename__ = 'events'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_type: Mapped[str] = mapped_column(String(50), default='user')
    actor_id: Mapped[str] = mapped_column(String(128), default='unknown')
    text: Mapped[str] = mapped_column(Text, default='')
    payload: Mapped[dict] = mapped_column(MYSQL_JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    memories: Mapped[list['Memory']] = relationship(
        back_populates='event',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )