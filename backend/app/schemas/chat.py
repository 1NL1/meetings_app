from uuid import UUID

from pydantic import BaseModel


class ChatQuestion(BaseModel):
    question: str
    scope: list[UUID] | None = None
    allow_web_search: bool = False


class SourceCitation(BaseModel):
    source_type: str
    source_id: UUID
    source_name: str
    chunk_text: str
    relevance_score: float


class ChatAnswer(BaseModel):
    answer: str
    sources: list[SourceCitation]
    used_external: bool = False
