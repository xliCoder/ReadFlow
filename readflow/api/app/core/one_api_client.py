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
