from app.services.chunk_service import Chunk


class VectorServiceError(Exception):
    pass


class VectorService:
    def __init__(self, milvus_uri: str, collection_name: str = 'readflow_chunks') -> None:
        self.milvus_uri = milvus_uri
        self.collection_name = collection_name
        self._client = None

    def _get_client(self):
        if self._client is None:
            from pymilvus import MilvusClient

            self._client = MilvusClient(uri=self.milvus_uri)
        return self._client

    def insert_chunks(
        self,
        source_id: str,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError('chunks and embeddings must have the same length')

        if not chunks:
            return 0

        client = self._get_client()

        if not client.has_collection(self.collection_name):
            from pymilvus import DataType

            schema = [
                {'name': 'id', 'dtype': DataType.INT64, 'is_primary': True, 'auto_id': True},
                {'name': 'source_id', 'dtype': DataType.VARCHAR, 'max_length': 64},
                {'name': 'chunk_index', 'dtype': DataType.INT64},
                {'name': 'text', 'dtype': DataType.VARCHAR, 'max_length': 4096},
                {'name': 'embedding', 'dtype': DataType.FLOAT_VECTOR, 'dim': len(embeddings[0])},
            ]
            client.create_collection(self.collection_name, schema=schema)

        records = [
            {
                'source_id': source_id,
                'chunk_index': chunk.chunk_index,
                'text': chunk.text[:4096],
                'embedding': embedding,
            }
            for chunk, embedding in zip(chunks, embeddings)
        ]

        try:
            client.insert(self.collection_name, records)
        except Exception as exc:
            raise VectorServiceError(f'Failed to insert chunks: {exc}') from exc

        return len(records)
