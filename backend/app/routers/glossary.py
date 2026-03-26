from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.glossary import GlossaryEntry
from app.models.user import User
from app.schemas.glossary import GlossaryEntryCreate, GlossaryEntryResponse

router = APIRouter()


@router.get("/", response_model=list[GlossaryEntryResponse])
async def list_glossary_entries(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(GlossaryEntry)
        .where(GlossaryEntry.user_id == current_user.id)
        .order_by(GlossaryEntry.category, GlossaryEntry.term)
    )
    return result.scalars().all()


@router.post("/", response_model=GlossaryEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_glossary_entry(
    data: GlossaryEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = GlossaryEntry(
        user_id=current_user.id,
        term=data.term,
        category=data.category,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_glossary_entry(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(GlossaryEntry).where(
            GlossaryEntry.id == entry_id,
            GlossaryEntry.user_id == current_user.id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    await db.delete(entry)
    await db.commit()
