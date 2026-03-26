from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MeetingCreate(BaseModel):
    title: str
    date: datetime
    template_id: UUID | None = None
    participants: list[str] | None = None


class MeetingUpdate(BaseModel):
    title: str | None = None
    date: datetime | None = None
    participants: list[str] | None = None


class MeetingResponse(BaseModel):
    id: UUID
    title: str
    date: datetime
    participants: list[str] | None = None
    raw_transcription: str | None = None
    report_markdown: str | None = None
    report_validated: bool
    template_id: UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportGenerateRequest(BaseModel):
    meeting_id: UUID


class ReportSave(BaseModel):
    report_markdown: str
