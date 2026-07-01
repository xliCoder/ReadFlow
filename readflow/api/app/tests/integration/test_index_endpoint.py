from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import ContentSource
from app.routers.content import one_api_client, vector_service


@pytest.mark.asyncio
async def test_index_valid_source(
    client: AsyncClient, db_session: AsyncSession, sample_pdf_bytes
):
    files = {'file': ('sample.pdf', sample_pdf_bytes, 'application/pdf')}
    upload_response = await client.post('/api/v1/content/upload', files=files)
    assert upload_response.status_code == 200
    source_id = upload_response.json()['source_id']

    with patch.object(one_api_client, 'embed', new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        with patch.object(vector_service, 'insert_chunks', return_value=2):
            response = await client.post(f'/api/v1/content/{source_id}/index')

    assert response.status_code == 200
    data = response.json()
    assert data['source_id'] == source_id
    assert data['status'] == 'indexed'
    assert data['chunk_count'] == 2

    result = await db_session.execute(
        select(ContentSource).where(ContentSource.id == source_id)
    )
    source = result.scalar_one_or_none()
    assert source is not None
    assert source.status == 'indexed'

    mock_embed.assert_awaited_once()


@pytest.mark.asyncio
async def test_index_source_not_found(client: AsyncClient):
    response = await client.post('/api/v1/content/nonexistent-id/index')

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_index_source_not_parsed(
    client: AsyncClient, db_session: AsyncSession, sample_pdf_bytes
):
    files = {'file': ('sample.pdf', sample_pdf_bytes, 'application/pdf')}
    upload_response = await client.post('/api/v1/content/upload', files=files)
    source_id = upload_response.json()['source_id']

    result = await db_session.execute(
        select(ContentSource).where(ContentSource.id == source_id)
    )
    source = result.scalar_one()
    source.status = 'indexed'
    await db_session.commit()

    response = await client.post(f'/api/v1/content/{source_id}/index')

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_index_embedding_failure(
    client: AsyncClient, db_session: AsyncSession, sample_pdf_bytes
):
    files = {'file': ('sample.pdf', sample_pdf_bytes, 'application/pdf')}
    upload_response = await client.post('/api/v1/content/upload', files=files)
    source_id = upload_response.json()['source_id']

    from app.core.one_api_client import OneAPIError

    with patch.object(one_api_client, 'embed', new_callable=AsyncMock) as mock_embed:
        mock_embed.side_effect = OneAPIError('upstream failure')
        response = await client.post(f'/api/v1/content/{source_id}/index')

    assert response.status_code == 502
    assert 'embedding' in response.json()['detail'].lower()


@pytest.mark.asyncio
async def test_index_vector_storage_failure(
    client: AsyncClient, db_session: AsyncSession, sample_pdf_bytes
):
    files = {'file': ('sample.pdf', sample_pdf_bytes, 'application/pdf')}
    upload_response = await client.post('/api/v1/content/upload', files=files)
    source_id = upload_response.json()['source_id']

    from app.services.vector_service import VectorServiceError

    with patch.object(one_api_client, 'embed', new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        with patch.object(
            vector_service, 'insert_chunks', side_effect=VectorServiceError('milvus down')
        ):
            response = await client.post(f'/api/v1/content/{source_id}/index')

    assert response.status_code == 502
    assert 'vector' in response.json()['detail'].lower()


@pytest.mark.asyncio
async def test_index_unexpected_failure_marks_source_failed(
    client: AsyncClient, db_session: AsyncSession, sample_pdf_bytes
):
    files = {'file': ('sample.pdf', sample_pdf_bytes, 'application/pdf')}
    upload_response = await client.post('/api/v1/content/upload', files=files)
    source_id = upload_response.json()['source_id']

    with patch('app.routers.content.chunk_service') as mock_chunk_service:
        mock_chunk_service.chunk_text.side_effect = ValueError('unexpected chunker error')
        response = await client.post(f'/api/v1/content/{source_id}/index')

    assert response.status_code == 500
    assert 'indexing failed' in response.json()['detail'].lower()

    result = await db_session.execute(
        select(ContentSource).where(ContentSource.id == source_id)
    )
    source = result.scalar_one()
    assert source.status == 'failed'


@pytest.mark.asyncio
async def test_index_empty_text_returns_zero_chunks(
    client: AsyncClient, db_session: AsyncSession, sample_pdf_bytes
):
    files = {'file': ('sample.pdf', sample_pdf_bytes, 'application/pdf')}
    upload_response = await client.post('/api/v1/content/upload', files=files)
    source_id = upload_response.json()['source_id']

    result = await db_session.execute(
        select(ContentSource).where(ContentSource.id == source_id)
    )
    source = result.scalar_one()
    source.extracted_text = ''
    await db_session.commit()

    response = await client.post(f'/api/v1/content/{source_id}/index')

    assert response.status_code == 200
    assert response.json()['chunk_count'] == 0
    assert response.json()['message'] == 'No chunks generated from empty text'
