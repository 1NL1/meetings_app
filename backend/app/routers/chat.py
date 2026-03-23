from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.chat import ChatAnswer, ChatQuestion
from app.services.rag import answer_question

router = APIRouter()


@router.post("/ask", response_model=ChatAnswer)
async def ask_question(
    data: ChatQuestion,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await answer_question(
        data.question, current_user.id, db, scope=data.scope, allow_web_search=data.allow_web_search
    )
