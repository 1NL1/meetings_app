import os
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_user, get_db
from app.models.glossary import GlossaryEntry
from app.models.meeting import Meeting
from app.models.template import Template
from app.models.user import User
from app.schemas.meeting import MeetingCreate, MeetingResponse, MeetingUpdate, ReportSave
from app.services.embedding import embed_and_store
from app.services.report_generator import generate_report
from app.services.transcription import transcribe_audio, transcribe_audio_stream

router = APIRouter()


@router.post("/", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    data: MeetingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = Meeting(
        title=data.title,
        date=data.date,
        template_id=data.template_id,
        participants=data.participants,
        user_id=current_user.id,
    )
    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)
    return meeting


@router.get("/", response_model=list[MeetingResponse])
async def list_meetings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Meeting).where(Meeting.user_id == current_user.id).order_by(Meeting.date.desc())
    )
    return result.scalars().all()


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = await _get_user_meeting(meeting_id, current_user.id, db)
    return meeting


@router.put("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: UUID,
    data: MeetingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = await _get_user_meeting(meeting_id, current_user.id, db)
    if data.title is not None:
        meeting.title = data.title
    if data.date is not None:
        meeting.date = data.date
    if data.participants is not None:
        meeting.participants = data.participants
    await db.commit()
    await db.refresh(meeting)
    return meeting


@router.post("/{meeting_id}/upload-audio", response_model=MeetingResponse)
async def upload_audio(
    meeting_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = await _get_user_meeting(meeting_id, current_user.id, db)

    # Save file to disk
    audio_dir = os.path.join(settings.upload_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "audio.webm")[1]
    file_path = os.path.join(audio_dir, f"{meeting_id}{ext}")
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    meeting.audio_file_path = f"audio/{meeting_id}{ext}"

    # Transcribe
    transcription = await transcribe_audio(file_path)
    meeting.raw_transcription = transcription

    await db.commit()
    await db.refresh(meeting)
    return meeting


@router.post("/{meeting_id}/generate-report", response_model=MeetingResponse)
async def generate_meeting_report(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = await _get_user_meeting(meeting_id, current_user.id, db)

    if not meeting.raw_transcription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transcription available. Upload and transcribe audio first.",
        )

    # Load template content
    template_content = ""
    if meeting.template_id:
        result = await db.execute(select(Template).where(Template.id == meeting.template_id))
        template = result.scalar_one_or_none()
        if template:
            template_content = template.content

    if not template_content:
        template_content = (
            "# Compte-rendu de réunion\n\n"
            "## Participants\n\n## Ordre du jour\n\n"
            "## Discussions\n\n## Décisions\n\n## Actions à suivre\n"
        )

    glossary_result = await db.execute(
        select(GlossaryEntry).where(GlossaryEntry.user_id == current_user.id)
    )
    glossary_terms = [e.term for e in glossary_result.scalars().all()]

    report = await generate_report(
        meeting.raw_transcription,
        template_content,
        participants=meeting.participants or [],
        glossary_terms=glossary_terms,
        title=meeting.title,
        date=meeting.date.strftime("%d/%m/%Y %H:%M"),
    )
    meeting.report_markdown = report

    await db.commit()
    await db.refresh(meeting)
    return meeting


@router.put("/{meeting_id}/template", response_model=MeetingResponse)
async def update_meeting_template(
    meeting_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = await _get_user_meeting(meeting_id, current_user.id, db)
    template_id = data.get("template_id")
    meeting.template_id = UUID(template_id) if template_id else None
    await db.commit()
    await db.refresh(meeting)
    return meeting


@router.put("/{meeting_id}/report", response_model=MeetingResponse)
async def save_report(
    meeting_id: UUID,
    data: ReportSave,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = await _get_user_meeting(meeting_id, current_user.id, db)
    meeting.report_markdown = data.report_markdown
    await db.commit()
    await db.refresh(meeting)
    return meeting


@router.put("/{meeting_id}/validate", response_model=MeetingResponse)
async def validate_report(
    meeting_id: UUID,
    data: ReportSave,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = await _get_user_meeting(meeting_id, current_user.id, db)
    meeting.report_markdown = data.report_markdown
    meeting.report_validated = True
    await db.commit()
    await db.refresh(meeting)

    # Index the validated report for RAG
    if meeting.report_markdown:
        await embed_and_store(meeting.report_markdown, "meeting", meeting.id, db)

    return meeting


@router.put("/{meeting_id}/invalidate", response_model=MeetingResponse)
async def invalidate_report(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = await _get_user_meeting(meeting_id, current_user.id, db)
    meeting.report_validated = False

    # Remove embeddings for this meeting
    from app.models.embedding import EmbeddingChunk

    result = await db.execute(
        select(EmbeddingChunk).where(
            EmbeddingChunk.source_type == "meeting",
            EmbeddingChunk.source_id == meeting_id,
        )
    )
    for chunk in result.scalars().all():
        await db.delete(chunk)

    await db.commit()
    await db.refresh(meeting)
    return meeting


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = await _get_user_meeting(meeting_id, current_user.id, db)

    # Remove embeddings for this meeting
    from app.models.embedding import EmbeddingChunk

    result = await db.execute(
        select(EmbeddingChunk).where(
            EmbeddingChunk.source_type == "meeting",
            EmbeddingChunk.source_id == meeting_id,
        )
    )
    for chunk in result.scalars().all():
        await db.delete(chunk)

    await db.delete(meeting)
    await db.commit()


@router.websocket("/{meeting_id}/transcribe")
async def websocket_transcribe(websocket: WebSocket, meeting_id: UUID):
    """WebSocket endpoint: receive audio chunks from browser, transcribe in real-time."""
    await websocket.accept()

    try:
        transcription = await transcribe_audio_stream(websocket)

        # Save transcription to DB
        from app.database import async_session

        async with async_session() as db:
            result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
            meeting = result.scalar_one_or_none()
            if meeting:
                meeting.raw_transcription = transcription
                await db.commit()
    except WebSocketDisconnect:
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


async def _get_user_meeting(meeting_id: UUID, user_id: UUID, db: AsyncSession) -> Meeting:
    result = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id, Meeting.user_id == user_id)
    )
    meeting = result.scalar_one_or_none()
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return meeting
