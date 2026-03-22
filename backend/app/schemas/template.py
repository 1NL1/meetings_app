from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TemplateCreate(BaseModel):
    name: str
    content: str


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None


class TemplateResponse(BaseModel):
    id: UUID
    name: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
