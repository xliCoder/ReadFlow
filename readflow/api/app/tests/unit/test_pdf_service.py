import asyncio
from io import BytesIO

import pytest
from pypdf import PdfWriter
from reportlab.pdfgen import canvas

from app.schemas.content import ContentParseResult
from app.services.pdf_service import PDFParseError, PDFService


def _make_pdf_bytes(texts: list[str]) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    for text in texts:
        c.drawString(100, 700, text)
        c.showPage()
    c.save()
    return buffer.getvalue()


def test_parse_valid_pdf():
    pdf_bytes = _make_pdf_bytes(['Hello, ReadFlow!', 'Page two.'])
    service = PDFService()
    result = asyncio.run(service.parse_pdf(pdf_bytes, 'hello.pdf'))

    assert isinstance(result, ContentParseResult)
    assert result.filename == 'hello.pdf'
    assert result.page_count == 2
    assert result.total_chars > 0
    assert 'Hello, ReadFlow!' in result.extracted_text_preview
    assert result.status == 'parsed'


def test_parse_empty_pdf():
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buffer = BytesIO()
    writer.write(buffer)

    service = PDFService()
    result = asyncio.run(service.parse_pdf(buffer.getvalue(), 'empty.pdf'))

    assert result.page_count == 1
    assert result.total_chars == 0
    assert result.status == 'parsed'


def test_parse_corrupted_pdf():
    service = PDFService()
    with pytest.raises(PDFParseError):
        asyncio.run(service.parse_pdf(b"not a pdf", 'broken.pdf'))


def test_parse_large_pdf_preview_truncated():
    large_text = 'word ' * 5000
    pdf_bytes = _make_pdf_bytes([large_text])
    service = PDFService()
    result = asyncio.run(service.parse_pdf(pdf_bytes, 'large.pdf'))

    assert result.total_chars > PDFService.PREVIEW_MAX_CHARS
    assert len(result.extracted_text_preview) <= PDFService.PREVIEW_MAX_CHARS + 3
    assert result.extracted_text_preview.endswith('...')
