from mistralai.client import Mistral
from mistralai.client.models.systemmessage import SystemMessage
from mistralai.client.models.usermessage import UserMessage

from app.config import settings

client = Mistral(api_key=settings.mistral_api_key)


async def generate_report(
    transcription: str,
    template_content: str,
    participants: str | None = None,
    title: str | None = None,
    date: str | None = None,
) -> str:
    """Generate a meeting report from a transcription using a template via Mistral Large."""
    context_lines = []
    if title:
        context_lines.append(f"Titre de la réunion : {title}")
    if date:
        context_lines.append(f"Date de la réunion : {date}")
    if participants:
        context_lines.append(f"Participants : {participants}")

    context_info = ""
    if context_lines:
        context_info = (
            "\n\nInformations sur la réunion :\n"
            + "\n".join(f"- {line}" for line in context_lines)
            + "\n\nInclus ces informations dans le compte-rendu. "
            "Attribue les interventions aux bons participants quand c'est possible."
        )

    system_prompt = (
        "Tu es un assistant de rédaction de comptes-rendus de réunion. "
        "Voici un template de compte-rendu :\n\n"
        f"{template_content}\n\n"
        "À partir de la transcription suivante, rédige le compte-rendu "
        "en suivant exactement la structure du template. "
        f"Rédige en Markdown.{context_info}"
    )
    messages: list[SystemMessage | UserMessage] = [
        SystemMessage(content=system_prompt),
        UserMessage(content=f"Transcription :\n\n{transcription}"),
    ]
    response = await client.chat.complete_async(
        model="mistral-large-latest",
        messages=messages,  # type: ignore[arg-type]
    )
    content = response.choices[0].message.content
    if isinstance(content, str):
        return content
    return str(content)
