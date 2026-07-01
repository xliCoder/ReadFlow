from app.core.one_api_client import OneAPIClient
from app.services.vector_service import VectorService


class ContextBuilder:
    DEFAULT_TOP_K = 5

    def __init__(
        self,
        one_api_client: OneAPIClient,
        vector_service: VectorService,
    ) -> None:
        self.one_api_client = one_api_client
        self.vector_service = vector_service

    async def build(self, source_id: str, question: str, top_k: int = DEFAULT_TOP_K) -> str:
        embeddings = await self.one_api_client.embed([question])
        question_embedding = embeddings[0] if embeddings else []

        chunks = self.vector_service.search(source_id, question_embedding, top_k)

        if not chunks:
            return 'No relevant context found for this question.'

        formatted = []
        for chunk in chunks:
            text = chunk.get('text', '')
            idx = chunk.get('chunk_index', 0)
            formatted.append(f'[Chunk {idx}] {text}')

        return '\n\n'.join(formatted)
