from pathlib import Path

from fastapi import WebSocket
from mistralai.client import Mistral

from app.config import settings

client = Mistral(api_key=settings.mistral_api_key)


async def transcribe_audio(file_path: str) -> str:
    """Upload an audio file to Voxtral and return the full transcription text."""
    path = Path(file_path)
    with open(path, "rb") as audio_file:
        result = await client.audio.transcriptions.complete_async(
            model="voxtral-mini-transcribe-2507",
            file={
                "file_name": path.name,
                "content": audio_file.read(),
            },
        )
    return str(result.text)


async def transcribe_audio_stream(websocket: WebSocket) -> str:
    """Receive audio chunks via WebSocket, accumulate them, transcribe, and stream back segments."""
    chunks: list[bytes] = []
    full_text = ""

    try:
        while True:
            data = await websocket.receive_bytes()

            # Client sends empty bytes to signal end of recording
            if len(data) == 0:
                break

            chunks.append(data)

            # Transcribe accumulated audio periodically (every ~5 chunks)
            if len(chunks) % 5 == 0:
                audio_blob = b"".join(chunks)
                try:
                    result = await client.audio.transcriptions.complete_async(
                        model="voxtral-mini-transcribe-2507",
                        file={
                            "file_name": "stream.webm",
                            "content": audio_blob,
                        },
                    )
                    full_text = str(result.text)
                    await websocket.send_json(
                        {
                            "type": "partial",
                            "text": full_text,
                        }
                    )
                except Exception:
                    pass

    except Exception:
        pass

    # Final transcription of all accumulated audio
    if chunks:
        audio_blob = b"".join(chunks)
        try:
            result = await client.audio.transcriptions.complete_async(
                model="voxtral-mini-transcribe-2507",
                file={
                    "file_name": "stream.webm",
                    "content": audio_blob,
                },
            )
            full_text = str(result.text)
        except Exception:
            pass

    await websocket.send_json(
        {
            "type": "final",
            "text": full_text,
        }
    )

    return full_text
