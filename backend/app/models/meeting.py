import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255))
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    audio_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_transcription: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    template_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("templates.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
