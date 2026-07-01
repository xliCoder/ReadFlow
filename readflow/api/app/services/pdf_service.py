import asyncio
from io import BytesIO

from pypdf import PdfReader

from app.schemas.content import ContentParseResult


class PDFParseError(Exception):
    pass


class PDFService:
    PREVIEW_MAX_CHARS = 2000

    async def parse_pdf(self, file_bytes: bytes, filename: str) -> ContentParseResult:
        return await asyncio.to_thread(self._parse_sync, file_bytes, filename)

    def _parse_sync(self, file_bytes: bytes, filename: str) -> ContentParseResult:
        try:
            reader = PdfReader(BytesIO(file_bytes))
            page_count = len(reader.pages)

            full_text = ''
            for page in reader.pages:
                page_text = page.extract_text() or ''
                if page_text:
                    full_text += page_text + '\n'

            total_chars = len(full_text)
            preview = full_text[: self.PREVIEW_MAX_CHARS]
            if total_chars > self.PREVIEW_MAX_CHARS:
                preview += '...'

            return ContentParseResult(
                filename=filename,
                page_count=page_count,
                total_chars=total_chars,
                extracted_text_preview=preview,
                extracted_text=full_text,
            )
        except Exception as exc:
            raise PDFParseError(f"Failed to parse PDF: {exc}") from exc


pdf_service = PDFService()
