from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    doc_type: str
    content_preview: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_preview(cls, doc: object) -> "DocumentResponse":
        content = getattr(doc, "content_text", None) or ""
        return cls(
            id=doc.id,  # type: ignore[attr-defined]
            filename=doc.filename,  # type: ignore[attr-defined]
            doc_type=doc.doc_type,  # type: ignore[attr-defined]
            content_preview=content[:200] if content else None,
            created_at=doc.created_at,  # type: ignore[attr-defined]
        )
