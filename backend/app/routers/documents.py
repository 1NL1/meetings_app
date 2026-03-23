import os
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_user, get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services.embedding import embed_and_store
from app.services.ocr import extract_text

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = "other",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid as uuid_mod

    doc_id = uuid_mod.uuid4()
    ext = os.path.splitext(file.filename or "file")[1]
    relative_path = f"documents/{doc_id}{ext}"

    # Save file to disk
    docs_dir = os.path.join(settings.upload_dir, "documents")
    os.makedirs(docs_dir, exist_ok=True)
    full_path = os.path.join(settings.upload_dir, relative_path)

    content = await file.read()
    with open(full_path, "wb") as f:
        f.write(content)

    # Extract text via OCR / parsing
    content_text = await extract_text(full_path, file.content_type)

    # Store in DB
    doc = Document(
        id=doc_id,
        user_id=current_user.id,
        filename=file.filename or "unknown",
        file_path=relative_path,
        content_text=content_text,
        doc_type=doc_type,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Embed for RAG
    if content_text:
        await embed_and_store(content_text, "document", doc.id, db)

    return DocumentResponse.from_orm_with_preview(doc)


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    return [DocumentResponse.from_orm_with_preview(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = await _get_user_document(document_id, current_user.id, db)
    return DocumentResponse.from_orm_with_preview(doc)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = await _get_user_document(document_id, current_user.id, db)
    # Clean up file
    full_path = os.path.join(settings.upload_dir, doc.file_path)
    if os.path.exists(full_path):
        os.remove(full_path)
    await db.delete(doc)
    await db.commit()


async def _get_user_document(document_id: UUID, user_id: UUID, db: AsyncSession) -> Document:
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc
