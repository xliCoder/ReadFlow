import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import ContentSource


@pytest.mark.asyncio
async def test_upload_valid_pdf(client: AsyncClient, db_session: AsyncSession, sample_pdf_bytes):
    files = {'file': ('sample.pdf', sample_pdf_bytes, 'application/pdf')}
    response = await client.post('/api/v1/content/upload', files=files)

    assert response.status_code == 200
    data = response.json()
    assert data['source_id']
    assert data['filename'] == 'sample.pdf'
    assert data['source_type'] == 'pdf'
    assert data['page_count'] == 2
    assert data['total_chars'] > 0
    assert 'Hello, ReadFlow!' in data['extracted_text_preview']
    assert data['status'] == 'parsed'
    assert data['file_size_bytes'] == len(sample_pdf_bytes)

    result = await db_session.execute(
        select(ContentSource).where(ContentSource.id == data['source_id'])
    )
    source = result.scalar_one_or_none()
    assert source is not None
    assert source.filename == 'sample.pdf'
    assert source.status == 'parsed'


@pytest.mark.asyncio
async def test_upload_invalid_file_type(client: AsyncClient):
    files = {'file': ('readme.txt', b"plain text content", 'text/plain')}
    response = await client.post('/api/v1/content/upload', files=files)

    assert response.status_code == 400
    assert 'pdf' in response.json()['detail'].lower()


@pytest.mark.asyncio
async def test_upload_file_too_large(client: AsyncClient):
    large_bytes = b"x" * (50 * 1024 * 1024 + 1)
    files = {'file': ('large.pdf', large_bytes, 'application/pdf')}
    response = await client.post('/api/v1/content/upload', files=files)

    assert response.status_code == 413


@pytest.mark.asyncio
async def test_upload_corrupted_pdf(client: AsyncClient, corrupted_pdf_bytes):
    files = {'file': ('broken.pdf', corrupted_pdf_bytes, 'application/pdf')}
    response = await client.post('/api/v1/content/upload', files=files)

    assert response.status_code == 422
    assert 'parse' in response.json()['detail'].lower()
