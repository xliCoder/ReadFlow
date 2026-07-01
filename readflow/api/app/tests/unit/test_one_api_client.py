from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.one_api_client import OneAPIClient, OneAPIError


@pytest.fixture
def client():
    return OneAPIClient(base_url='http://localhost:3000', api_key='test-key')


@pytest.mark.asyncio
async def test_stream_chat_yields_sse_lines(client: OneAPIClient):
    mock_response = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_response.raise_for_status = MagicMock()

    async def _line_iter():
        yield 'data: {"choices": [{"delta": {"content": "Hi"}}]}'
        yield ''

    mock_response.aiter_lines = _line_iter

    with patch.object(client._client, 'stream', return_value=mock_response):
        events = []
        async for event in client.stream_chat([{'role': 'user', 'content': 'hi'}]):
            events.append(event)

    assert len(events) == 1
    assert 'data:' in events[0]


@pytest.mark.asyncio
async def test_stream_chat_error_raises(client: OneAPIClient):
    with patch.object(
        client._client, 'stream', side_effect=Exception('connection refused')
    ):
        with pytest.raises(OneAPIError):
            async for _ in client.stream_chat([{'role': 'user', 'content': 'hi'}]):
                pass
