import base64
import mimetypes
from pathlib import Path

from mistralai.client import Mistral

from app.config import settings

client = Mistral(api_key=settings.mistral_api_key)


async def extract_text(file_path: str, mime_type: str | None = None) -> str:
    """Extract text from a file using Mistral OCR, python-docx, or direct read."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if mime_type is None:
        mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

    # Plain text / markdown: direct read
    if suffix in (".txt", ".md"):
        return path.read_text(encoding="utf-8")

    # Word documents
    if suffix == ".docx":
        return _extract_docx(path)

    # PDF and images: use Mistral OCR (Pixtral)
    if suffix == ".pdf":
        return await _ocr_pdf(path)

    if suffix in (".png", ".jpg", ".jpeg", ".webp", ".tiff"):
        return await _ocr_image(path, mime_type)

    return path.read_text(encoding="utf-8", errors="replace")


def _extract_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


async def _ocr_pdf(path: Path) -> str:
    """Use Mistral OCR to extract text from a PDF."""
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")

    result = await client.ocr.process_async(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": f"data:application/pdf;base64,{data}",
        },
    )
    pages_text = [page.markdown for page in result.pages]
    return "\n\n".join(pages_text)


async def _ocr_image(path: Path, mime_type: str) -> str:
    """Use Mistral OCR to extract text from an image."""
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")

    result = await client.ocr.process_async(
        model="mistral-ocr-latest",
        document={
            "type": "image_url",
            "image_url": f"data:{mime_type};base64,{data}",
        },
    )
    pages_text = [page.markdown for page in result.pages]
    return "\n\n".join(pages_text)
