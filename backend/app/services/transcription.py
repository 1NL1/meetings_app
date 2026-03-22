from pathlib import Path

from mistralai.client import Mistral

from app.config import settings

client = Mistral(api_key=settings.mistral_api_key)


async def transcribe_audio(file_path: str) -> str:
    """Upload an audio file to Voxtral and return the full transcription text."""
    path = Path(file_path)
    with open(path, "rb") as audio_file:
        result = await client.audio.transcriptions.complete_async(
            model="mistral-large-latest",
            file={
                "file_name": path.name,
                "content": audio_file.read(),
            },
        )
    return str(result.text)
