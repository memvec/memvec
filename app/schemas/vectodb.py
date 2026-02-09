from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Literal

from app.models.memory import Memory

class VectorDBUpsertItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    existing_memory_id: int | None = None  
    memory_exists: bool = Field(default=False, description="Indicates if a similar memory already exists in the vector database.")
    