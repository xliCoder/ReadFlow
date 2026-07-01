from collections.abc import AsyncIterator

from app.config import settings
from app.core.one_api_client import OneAPIClient
from app.services.context_builder import ContextBuilder


class ChatService:
    def __init__(
        self,
        one_api_client: OneAPIClient,
        context_builder: ContextBuilder,
    ) -> None:
        self.one_api_client = one_api_client
        self.context_builder = context_builder

    async def stream_chat(
        self,
        source_id: str,
        question: str,
    ) -> AsyncIterator[str]:
        context = await self.context_builder.build(source_id, question)
        messages = self._build_messages(question, context)

        async for event in self.one_api_client.stream_chat(
            messages,
            model=settings.chat_model,
        ):
            yield event

    def _build_messages(self, question: str, context: str) -> list[dict]:
        system_prompt = (
            'You are a helpful reading assistant. Use the provided context '
            'to answer the question. If the context does not contain the answer, say so.'
        )
        return [
            {'role': 'system', 'content': system_prompt},
            {
                'role': 'user',
                'content': f'Context:\n{context}\n\nQuestion: {question}',
            },
        ]
