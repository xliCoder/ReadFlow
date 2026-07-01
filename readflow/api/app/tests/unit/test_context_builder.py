from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.context_builder import ContextBuilder


@pytest.fixture
def context_builder():
    one_api_client = MagicMock()
    one_api_client.embed = AsyncMock()
    vector_service = MagicMock()
    return ContextBuilder(one_api_client=one_api_client, vector_service=vector_service)


@pytest.mark.asyncio
async def test_build_returns_formatted_context(context_builder: ContextBuilder):
    context_builder.one_api_client.embed.return_value = [[0.1, 0.2, 0.3]]
    context_builder.vector_service.search.return_value = [
        {'chunk_index': 0, 'text': 'First relevant chunk.', 'distance': 0.1},
        {'chunk_index': 1, 'text': 'Second relevant chunk.', 'distance': 0.2},
    ]

    context = await context_builder.build('source-1', 'what is this about?', top_k=3)

    assert 'First relevant chunk.' in context
    assert 'Second relevant chunk.' in context
    context_builder.vector_service.search.assert_called_once_with(
        'source-1', [0.1, 0.2, 0.3], 3
    )


@pytest.mark.asyncio
async def test_build_empty_results(context_builder: ContextBuilder):
    context_builder.one_api_client.embed.return_value = [[0.1, 0.2, 0.3]]
    context_builder.vector_service.search.return_value = []

    context = await context_builder.build('source-1', 'unknown topic')

    assert 'No relevant context found' in context


@pytest.mark.asyncio
async def test_build_uses_default_top_k(context_builder: ContextBuilder):
    context_builder.one_api_client.embed.return_value = [[0.1, 0.2, 0.3]]
    context_builder.vector_service.search.return_value = []

    await context_builder.build('source-1', 'question')

    context_builder.vector_service.search.assert_called_once_with(
        'source-1', [0.1, 0.2, 0.3], 5
    )


@pytest.mark.asyncio
async def test_build_empty_question_uses_empty_embedding(context_builder: ContextBuilder):
    context_builder.one_api_client.embed.return_value = [[]]
    context_builder.vector_service.search.return_value = []

    await context_builder.build('source-1', '')

    context_builder.one_api_client.embed.assert_awaited_once_with([''])
    context_builder.vector_service.search.assert_called_once_with('source-1', [], 5)
