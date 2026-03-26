import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.database import engine
from app.routers import auth, chat, documents, meetings, templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Retry loop pour attendre que PostgreSQL soit prêt
    retries = 10  # nombre de tentatives
    delay = 3  # secondes entre chaque tentative
    for attempt in range(1, retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            print("✅ Database is ready")
            break
        except OperationalError:
            print(f"⚠️ Database not ready, retrying {attempt}/{retries}...")
            await asyncio.sleep(delay)
    else:
        raise RuntimeError("Database is not ready after multiple retries")

    yield


app = FastAPI(title="MeetWise", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(meetings.router, prefix="/meetings", tags=["meetings"])
app.include_router(templates.router, prefix="/templates", tags=["templates"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
