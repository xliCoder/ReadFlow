from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.one_api_client import OneAPIClient, OneAPIError
from app.services.chunk_service import Chunk
from app.services.vector_service import VectorService, VectorServiceError


class TestOneAPIClient:
    @pytest.fixture
    def client(self):
        return OneAPIClient(base_url='http://localhost:3000', api_key='test-key')

    @pytest.mark.asyncio
    async def test_embed_returns_embeddings(self, client: OneAPIClient):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'embedding': [0.1, 0.2, 0.3], 'index': 0},
                {'embedding': [0.4, 0.5, 0.6], 'index': 1},
            ]
        }
        mock_response.raise_for_status.return_value = None

        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await client.embed(['hello', 'world'], model='bge-m3')

        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]
        mock_post.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_embed_empty_input_returns_empty(self, client: OneAPIClient):
        result = await client.embed([])

        assert result == []

    @pytest.mark.asyncio
    async def test_embed_api_error_raises(self, client: OneAPIClient):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception('upstream error')

        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(OneAPIError):
                await client.embed(['hello'])


class TestVectorService:
    @pytest.fixture
    def service(self):
        return VectorService(milvus_uri='http://localhost:19530')

    def test_insert_chunks_creates_collection_and_inserts(self, service: VectorService):
        chunks = [
            Chunk(text='first chunk', chunk_index=0, token_count=2),
            Chunk(text='second chunk', chunk_index=1, token_count=2),
        ]
        embeddings = [[0.1, 0.2], [0.3, 0.4]]

        mock_milvus = MagicMock()
        mock_milvus.has_collection.return_value = False

        with patch('pymilvus.MilvusClient', return_value=mock_milvus):
            inserted = service.insert_chunks('source-1', chunks, embeddings)

        assert inserted == 2
        mock_milvus.create_collection.assert_called_once()
        mock_milvus.insert.assert_called_once()

    def test_insert_chunks_empty_list_returns_zero(self, service: VectorService):
        with patch('pymilvus.MilvusClient') as mock_client:
            inserted = service.insert_chunks('source-1', [], [])

        assert inserted == 0
        mock_client.assert_not_called()

    def test_insert_chunks_length_mismatch_raises(self, service: VectorService):
        chunks = [Chunk(text='only chunk', chunk_index=0, token_count=2)]
        embeddings = [[0.1, 0.2], [0.3, 0.4]]

        with pytest.raises(ValueError):
            service.insert_chunks('source-1', chunks, embeddings)

    def test_insert_chunks_milvus_error_raises(self, service: VectorService):
        chunks = [Chunk(text='first chunk', chunk_index=0, token_count=2)]
        embeddings = [[0.1, 0.2]]

        mock_milvus = MagicMock()
        mock_milvus.has_collection.return_value = True
        mock_milvus.insert.side_effect = Exception('connection refused')

        with patch('pymilvus.MilvusClient', return_value=mock_milvus):
            with pytest.raises(VectorServiceError):
                service.insert_chunks('source-1', chunks, embeddings)

    def test_search_returns_flattened_results(self, service: VectorService):
        mock_milvus = MagicMock()
        mock_milvus.has_collection.return_value = True
        mock_milvus.search.return_value = [
            [
                {
                    'entity': {
                        'source_id': 'source-1',
                        'chunk_index': 0,
                        'text': 'first chunk',
                    },
                    'distance': 0.1,
                },
                {
                    'entity': {
                        'source_id': 'source-1',
                        'chunk_index': 1,
                        'text': 'second chunk',
                    },
                    'distance': 0.2,
                },
            ]
        ]

        with patch('pymilvus.MilvusClient', return_value=mock_milvus):
            results = service.search('source-1', [0.1, 0.2, 0.3], top_k=2)

        assert len(results) == 2
        assert results[0]['chunk_index'] == 0
        assert results[1]['text'] == 'second chunk'
        mock_milvus.search.assert_called_once()

    def test_search_no_collection_returns_empty(self, service: VectorService):
        mock_milvus = MagicMock()
        mock_milvus.has_collection.return_value = False

        with patch('pymilvus.MilvusClient', return_value=mock_milvus):
            results = service.search('source-1', [0.1, 0.2, 0.3])

        assert results == []
        mock_milvus.search.assert_not_called()

    def test_search_empty_results_returns_empty(self, service: VectorService):
        mock_milvus = MagicMock()
        mock_milvus.has_collection.return_value = True
        mock_milvus.search.return_value = []

        with patch('pymilvus.MilvusClient', return_value=mock_milvus):
            results = service.search('source-1', [0.1, 0.2, 0.3])

        assert results == []

    def test_search_milvus_error_raises(self, service: VectorService):
        mock_milvus = MagicMock()
        mock_milvus.has_collection.return_value = True
        mock_milvus.search.side_effect = Exception('connection refused')

        with patch('pymilvus.MilvusClient', return_value=mock_milvus):
            with pytest.raises(VectorServiceError):
                service.search('source-1', [0.1, 0.2, 0.3])

    def test_format_filter_escapes_quotes(self):
        raw_filter = VectorService._format_filter('source"1')
        assert raw_filter == 'source_id == "source\\"1"'
