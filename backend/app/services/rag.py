import re
from uuid import UUID

from mistralai.client import Mistral
from mistralai.client.models.systemmessage import SystemMessage
from mistralai.client.models.usermessage import UserMessage
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.document import Document
from app.models.meeting import Meeting
from app.schemas.chat import ChatAnswer, SourceCitation
from app.services.external_search import search_external

client = Mistral(api_key=settings.mistral_api_key)

TOP_K = 5
SIMILARITY_THRESHOLD = 0.7


async def answer_question(
    question: str,
    user_id: UUID,
    db: AsyncSession,
    scope: list[UUID] | None = None,
    allow_web_search: bool = False,
) -> ChatAnswer:
    """RAG pipeline: embed question, retrieve chunks, generate answer with citations."""

    # 1. Embed the question
    embed_response = await client.embeddings.create_async(
        model="mistral-embed",
        inputs=[question],
    )
    question_embedding = embed_response.data[0].embedding or []

    # 2. Retrieve top-K chunks by cosine similarity (with optional scope filter)
    embedding_str = "[" + ",".join(str(x) for x in question_embedding) + "]"

    if scope:
        scope_str = ",".join(f"'{str(s)}'" for s in scope)
        query = text(f"""
            SELECT id, source_type, source_id, chunk_index, chunk_text,
                   1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM embedding_chunks
            WHERE source_id IN ({scope_str})
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
            """)
    else:
        query = text("""
            SELECT id, source_type, source_id, chunk_index, chunk_text,
                   1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM embedding_chunks
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
            """)

    result = await db.execute(query, {"embedding": embedding_str, "limit": TOP_K})
    rows = result.fetchall()

    # 3. Check if internal results are sufficient
    used_external = False
    max_similarity = max((row.similarity for row in rows), default=0.0)

    context_parts: list[str] = []
    source_map: list[dict[str, object]] = []

    # Only keep chunks above the threshold
    relevant_rows = [row for row in rows if row.similarity >= SIMILARITY_THRESHOLD]
    for i, row in enumerate(relevant_rows):
        source_name = await _get_source_name(str(row.source_type), row.source_id, db)
        context_parts.append(f"[source:{i}] ({source_name}) {row.chunk_text}")
        source_map.append(
            {
                "source_type": row.source_type,
                "source_id": row.source_id,
                "chunk_text": row.chunk_text,
                "similarity": float(row.similarity),
                "source_name": source_name,
            }
        )

    # 4. Fallback to external search if allowed and no relevant internal results
    if allow_web_search and (not relevant_rows or max_similarity < SIMILARITY_THRESHOLD):
        external_results = await search_external(question)
        if external_results:
            used_external = True
            for ext in external_results:
                idx = len(context_parts)
                snippet = f"[source:{idx}] (Externe — {ext['title']}) {ext['snippet']}"
                context_parts.append(snippet)
                source_map.append(
                    {
                        "source_type": "external",
                        "source_id": UUID("00000000-0000-0000-0000-000000000000"),
                        "chunk_text": f"{ext['title']}: {ext['snippet']}",
                        "similarity": 0.0,
                        "source_name": ext["title"],
                    }
                )

    if not context_parts:
        return ChatAnswer(answer="Aucun document pertinent trouvé.", sources=[])

    context = "\n\n".join(context_parts)

    # 5. Generate answer with Mistral Small
    if used_external:
        system_prompt = (
            "Tu es un assistant qui répond aux questions en te basant sur les sources fournies. "
            "Certaines sources proviennent de documents internes, d'autres de recherches externes "
            "(Wikipedia, web). Utilise toutes les sources disponibles pour répondre. "
            "Cite tes sources avec le format [source:N] dans ta réponse."
        )
    else:
        system_prompt = (
            "Tu es un assistant qui répond aux questions en te basant sur les documents fournis. "
            "Cite tes sources avec le format [source:N] dans ta réponse. "
            "Si tu ne trouves pas la réponse dans les documents, dis-le clairement."
        )

    messages: list[SystemMessage | UserMessage] = [
        SystemMessage(content=system_prompt),
        UserMessage(content=f"Question : {question}\n\nContexte :\n{context}"),
    ]

    response = await client.chat.complete_async(
        model="mistral-small-latest",
        messages=messages,  # type: ignore[arg-type]
    )
    answer_text = response.choices[0].message.content
    if not isinstance(answer_text, str):
        answer_text = str(answer_text)

    # 6. Parse [source:N] citations from the answer
    cited_indices = set(int(m) for m in re.findall(r"\[source:(\d+)\]", answer_text))

    # 7. Build SourceCitation objects for cited sources
    sources: list[SourceCitation] = []
    for i in cited_indices:
        if i >= len(source_map):
            continue
        src = source_map[i]
        source_id = src["source_id"]
        assert isinstance(source_id, UUID)

        source_name = str(src.get("source_name", "Source inconnue"))
        sources.append(
            SourceCitation(
                source_type=str(src["source_type"]),
                source_id=source_id,
                source_name=source_name,
                chunk_text=str(src["chunk_text"]),
                relevance_score=float(str(src["similarity"])),
            )
        )

    return ChatAnswer(answer=answer_text, sources=sources, used_external=used_external)


async def _get_source_name(source_type: str, source_id: UUID, db: AsyncSession) -> str:
    """Resolve the human-readable name of a source."""
    if source_type == "meeting":
        result = await db.execute(
            select(Meeting.title, Meeting.date).where(Meeting.id == source_id)
        )
        row = result.one_or_none()
        if row:
            title, date = row
            date_str = date.strftime("%d/%m/%Y") if date else ""
            return f"{title} (réunion du {date_str})" if date_str else str(title)
        return "Réunion inconnue"
    elif source_type == "document":
        result = await db.execute(select(Document.filename).where(Document.id == source_id))
        filename = result.scalar_one_or_none()
        return str(filename) if filename else "Document inconnu"
    return "Source inconnue"
