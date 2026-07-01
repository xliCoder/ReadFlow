from unittest.mock import MagicMock, patch

import pytest

from app.routers import chat as chat_router_module
from app.routers.chat import _stream_response


@pytest.mark.asyncio
async def test_stream_response_yields_error_on_one_api_error():
    from app.core.one_api_client import OneAPIError

    chat_service_mock = MagicMock()
    chat_service_mock.stream_chat.return_value = _async_failing_generator(OneAPIError('model down'))

    with patch.object(chat_router_module, 'chat_service', chat_service_mock):
        events = []
        async for event in _stream_response('source-1', 'q'):
            events.append(event)

    assert len(events) == 1
    assert 'event: error' in events[0]
    assert 'model down' in events[0]


@pytest.mark.asyncio
async def test_stream_response_yields_error_on_unexpected_error():
    chat_service_mock = MagicMock()
    chat_service_mock.stream_chat.return_value = _async_failing_generator(ValueError('unexpected'))

    with patch.object(chat_router_module, 'chat_service', chat_service_mock):
        events = []
        async for event in _stream_response('source-1', 'q'):
            events.append(event)

    assert len(events) == 1
    assert 'event: error' in events[0]
    assert 'unexpected' in events[0]


def _async_failing_generator(exc: Exception):
    async def _gen():
        raise exc
        yield ''  # pragma: no cover

    return _gen()
