from mistralai.client import Mistral

from app.config import settings

client = Mistral(api_key=settings.mistral_api_key)


async def generate_report(transcription: str, template_content: str) -> str:
    """Generate a meeting report from a transcription using a template via Mistral Large."""
    system_prompt = (
        "Tu es un assistant de rédaction de comptes-rendus de réunion. "
        "Voici un template de compte-rendu :\n\n"
        f"{template_content}\n\n"
        "À partir de la transcription suivante, rédige le compte-rendu "
        "en suivant exactement la structure du template. "
        "Rédige en Markdown."
    )
    response = await client.chat.complete_async(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Transcription :\n\n{transcription}"},
        ],
    )
    return response.choices[0].message.content
