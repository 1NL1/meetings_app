from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TemplateCreate(BaseModel):
    name: str
    content: str


class TemplateUpdate(BaseModel):
    name: str | None = None
    content: str | None = None


class TemplateResponse(BaseModel):
    id: UUID
    name: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
