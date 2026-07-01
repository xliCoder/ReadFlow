from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.chat_service import ChatService


@pytest.fixture
def chat_service():
    one_api_client = MagicMock()
    one_api_client.stream_chat = MagicMock(return_value=_async_iterator(['hello', 'world']))
    context_builder = MagicMock()
    context_builder.build = AsyncMock(return_value='relevant context')
    return ChatService(
        one_api_client=one_api_client,
        context_builder=context_builder,
    )


def _async_iterator(items: list[str]) -> AsyncIterator[str]:
    async def _gen():
        for item in items:
            yield item

    return _gen()


@pytest.mark.asyncio
async def test_stream_chat_yields_events(chat_service: ChatService):
    events = []
    async for event in chat_service.stream_chat('source-1', 'what is this?'):
        events.append(event)

    assert events == ['hello', 'world']


@pytest.mark.asyncio
async def test_stream_chat_builds_context(chat_service: ChatService):
    async for _ in chat_service.stream_chat('source-1', 'what is this?'):
        pass

    chat_service.context_builder.build.assert_awaited_once_with('source-1', 'what is this?')


@pytest.mark.asyncio
async def test_stream_chat_passes_system_and_user_messages(chat_service: ChatService):
    async for _ in chat_service.stream_chat('source-1', 'what is this?'):
        pass

    call_args = chat_service.one_api_client.stream_chat.call_args
    messages = call_args.kwargs.get('messages') or call_args.args[0]
    assert any(msg['role'] == 'system' for msg in messages)
    assert any(msg['role'] == 'user' and 'what is this?' in msg['content'] for msg in messages)
    assert any('relevant context' in msg['content'] for msg in messages)


@pytest.mark.asyncio
async def test_stream_chat_empty_question(chat_service: ChatService):
    chat_service.context_builder.build.return_value = ''
    chat_service.one_api_client.stream_chat.return_value = _async_iterator([])

    events = []
    async for event in chat_service.stream_chat('source-1', ''):
        events.append(event)

    assert events == []
    chat_service.context_builder.build.assert_awaited_once_with('source-1', '')


@pytest.mark.asyncio
async def test_stream_chat_uses_configured_model(chat_service: ChatService):
    async for _ in chat_service.stream_chat('source-1', 'what is this?'):
        pass

    call_args = chat_service.one_api_client.stream_chat.call_args
    model = call_args.kwargs.get('model')
    assert model == 'gpt-4o-mini'
