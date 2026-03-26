from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class GlossaryEntryCreate(BaseModel):
    term: str
    category: str | None = None


class GlossaryEntryResponse(BaseModel):
    id: UUID
    term: str
    category: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
