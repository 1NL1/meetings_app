from uuid import UUID

from mistralai.client import Mistral
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.embedding import EmbeddingChunk

client = Mistral(api_key=settings.mistral_api_key)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def _split_into_chunks(text: str) -> list[str]:
    """Split text into chunks of ~CHUNK_SIZE tokens (approximated by words) with overlap."""
    words = text.split()
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + CHUNK_SIZE
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - CHUNK_OVERLAP
    return chunks


async def embed_and_store(
    text: str,
    source_type: str,
    source_id: UUID,
    db: AsyncSession,
) -> None:
    """Split text into chunks, compute embeddings via Mistral Embed, store in DB."""
    chunks = _split_into_chunks(text)
    if not chunks:
        return

    # Batch embed all chunks
    response = await client.embeddings.create_async(
        model="mistral-embed",
        inputs=chunks,
    )

    for i, embedding_data in enumerate(response.data):
        chunk_obj = EmbeddingChunk(
            source_type=source_type,
            source_id=source_id,
            chunk_index=i,
            chunk_text=chunks[i],
            embedding=embedding_data.embedding,
        )
        db.add(chunk_obj)

    await db.commit()
