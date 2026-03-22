from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class MeetingCreate(BaseModel):
    title: str
    date: datetime
    template_id: UUID | None = None


class MeetingResponse(BaseModel):
    id: UUID
    title: str
    date: datetime
    raw_transcription: Optional[str] = None
    report_markdown: Optional[str] = None
    report_validated: bool
    template_id: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportGenerateRequest(BaseModel):
    meeting_id: UUID


class ReportSave(BaseModel):
    report_markdown: str
