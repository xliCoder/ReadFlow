from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.routers.chat import chat_service


@pytest.mark.asyncio
async def test_chat_stream_returns_sse_events(client: AsyncClient):
    with patch.object(
        chat_service.context_builder.vector_service, 'search', return_value=[]
    ):
        with patch.object(
            chat_service.context_builder.one_api_client, 'embed', new_callable=AsyncMock
        ) as mock_embed:
            mock_embed.return_value = [[0.1, 0.2, 0.3]]

            async def _mock_stream():
                yield 'data: {"choices": [{"delta": {"content": "Hello"}}]}\n\n'
                yield 'data: {"choices": [{"delta": {"content": "!"}}]}\n\n'

            with patch.object(
                chat_service.one_api_client, 'stream_chat', return_value=_mock_stream()
            ):
                response = await client.post(
                    '/api/v1/chat',
                    json={'source_id': 'source-1', 'question': 'hello?'},
                )

    assert response.status_code == 200
    assert 'text/event-stream' in response.headers.get('content-type', '')
    body = response.text
    assert 'data:' in body
    assert 'Hello' in body


@pytest.mark.asyncio
async def test_chat_embedding_failure_returns_502(client: AsyncClient):
    from app.core.one_api_client import OneAPIError

    with patch.object(
        chat_service.context_builder.one_api_client, 'embed', new_callable=AsyncMock
    ) as mock_embed:
        mock_embed.side_effect = OneAPIError('embed failed')
        response = await client.post(
            '/api/v1/chat',
            json={'source_id': 'source-1', 'question': 'hello?'},
        )

    assert response.status_code == 502
    assert 'embedding' in response.json()['detail'].lower()


@pytest.mark.asyncio
async def test_chat_retrieval_failure_returns_502(client: AsyncClient):
    from app.services.vector_service import VectorServiceError

    with patch.object(
        chat_service.context_builder.vector_service, 'search', side_effect=VectorServiceError('milvus down')
    ):
        with patch.object(
            chat_service.context_builder.one_api_client, 'embed', new_callable=AsyncMock
        ) as mock_embed:
            mock_embed.return_value = [[0.1, 0.2, 0.3]]
            response = await client.post(
                '/api/v1/chat',
                json={'source_id': 'source-1', 'question': 'hello?'},
            )

    assert response.status_code == 502
    assert 'retrieval' in response.json()['detail'].lower()


@pytest.mark.asyncio
async def test_chat_missing_question_returns_422(client: AsyncClient):
    response = await client.post('/api/v1/chat', json={'source_id': 'source-1'})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_missing_source_id_returns_422(client: AsyncClient):
    response = await client.post('/api/v1/chat', json={'question': 'hello?'})

    assert response.status_code == 422
