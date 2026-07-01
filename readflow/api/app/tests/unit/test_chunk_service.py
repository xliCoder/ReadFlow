import pytest

from app.services.chunk_service import Chunk, ChunkService


class TestChunkService:
    def test_chunk_small_text_returns_single_chunk(self):
        service = ChunkService()
        text = 'Short text.'

        chunks = service.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].chunk_index == 0

    def test_chunk_text_split_by_size(self):
        service = ChunkService(chunk_size=20, chunk_overlap=0)
        text = ' '.join(['word'] * 50)

        chunks = service.chunk_text(text)

        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.text) <= 20

    def test_chunk_text_overlap(self):
        service = ChunkService(chunk_size=20, chunk_overlap=5)
        text = ' '.join(['word'] * 50)

        chunks = service.chunk_text(text)

        assert len(chunks) > 1
        for i in range(1, len(chunks)):
            prev_end = chunks[i - 1].text[-service.chunk_overlap :]
            assert any(part in chunks[i].text for part in prev_end.split())

    def test_chunk_text_indexes_are_sequential(self):
        service = ChunkService(chunk_size=10, chunk_overlap=0)
        text = ' '.join(['word'] * 30)

        chunks = service.chunk_text(text)

        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_chunk_empty_text_returns_empty_list(self):
        service = ChunkService()

        chunks = service.chunk_text('')

        assert chunks == []

    def test_chunk_text_preserves_paragraph_boundaries_when_possible(self):
        service = ChunkService(chunk_size=100, chunk_overlap=0)
        paragraphs = ['First paragraph with several words.', 'Second paragraph with more words.']
        text = '\n\n'.join(paragraphs)

        chunks = service.chunk_text(text)

        assert len(chunks) == 2
        assert paragraphs[0] in chunks[0].text
        assert paragraphs[1] in chunks[1].text

    def test_chunk_text_uses_default_size_when_not_specified(self):
        service = ChunkService()
        long_text = 'x' * 3000

        chunks = service.chunk_text(long_text)

        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.text) <= ChunkService.DEFAULT_CHUNK_SIZE

    def test_chunk_overlap_less_than_chunk_size(self):
        with pytest.raises(ValueError):
            ChunkService(chunk_size=10, chunk_overlap=10)

    def test_chunk_token_count_estimated(self):
        service = ChunkService(chunk_size=20, chunk_overlap=0)
        text = 'hello world test'

        chunks = service.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0].token_count is not None
        assert chunks[0].token_count > 0
