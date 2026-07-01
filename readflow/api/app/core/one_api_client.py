from collections.abc import AsyncIterator

import httpx


class OneAPIError(Exception):
    pass


class OneAPIClient:
    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=60.0)

    async def embed(
        self,
        texts: list[str],
        model: str = 'text-embedding-3-small',
    ) -> list[list[float]]:
        if not texts:
            return []

        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        payload = {
            'model': model,
            'input': texts,
        }

        try:
            response = await self._client.post(
                f'{self.base_url}/v1/embeddings',
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
        except Exception as exc:
            raise OneAPIError(f'Embedding request failed: {exc}') from exc

        data = response.json().get('data', [])
        sorted_data = sorted(data, key=lambda item: item.get('index', 0))
        return [item['embedding'] for item in sorted_data]

    async def stream_chat(
        self,
        messages: list[dict],
        model: str = 'gpt-4o-mini',
    ) -> AsyncIterator[str]:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
        }
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        payload = {
            'model': model,
            'messages': messages,
            'stream': True,
        }

        try:
            async with self._client.stream(
                'POST',
                f'{self.base_url}/v1/chat/completions',
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        yield line
        except Exception as exc:
            raise OneAPIError(f'Stream chat request failed: {exc}') from exc
