from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Literal

MemoryType = Literal['fact', 'preference', 'goal', 'plan', 'constraint', 'episode']
MemoryScope = Literal['profile', 'session']

class QualifiedMemory(BaseModel):
    model_config = ConfigDict(extra='forbid')
    type: MemoryType
    scope: MemoryScope
    key: str
    value: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)

class MemoryQualification(BaseModel):
    model_config = ConfigDict(extra='forbid')
    memories: list[QualifiedMemory] = Field(default_factory=list)
