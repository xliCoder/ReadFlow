import re
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    chunk_index: int
    token_count: int | None = None


class ChunkService:
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200
    _BOUNDARY_SEPARATORS = ['\n\n', '\n', '. ', '! ', '? ', ' ']

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError('chunk_overlap must be less than chunk_size')
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> list[Chunk]:
        if not text:
            return []

        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        raw_chunks: list[str] = []

        for paragraph in paragraphs:
            if len(paragraph) <= self.chunk_size:
                raw_chunks.append(paragraph)
                continue
            raw_chunks.extend(self._split_long_text(paragraph))

        return [
            Chunk(
                text=chunk_text,
                chunk_index=idx,
                token_count=self._estimate_token_count(chunk_text),
            )
            for idx, chunk_text in enumerate(raw_chunks)
        ]

    def _split_long_text(self, text: str) -> list[str]:
        chunks: list[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            if end < text_len:
                end = self._find_boundary(text, start, end)

            chunks.append(text[start:end].strip())
            start = end
            if start < text_len:
                start = max(start - self.chunk_overlap, 0)

        return [c for c in chunks if c]

    def _find_boundary(self, text: str, start: int, preferred_end: int) -> int:
        search_start = preferred_end
        search_end = max(start, preferred_end - self.chunk_size // 2)

        for separator in self._BOUNDARY_SEPARATORS:
            idx = text.rfind(separator, search_end, search_start)
            if idx != -1:
                return idx + len(separator)

        return preferred_end

    def _estimate_token_count(self, text: str) -> int:
        return max(1, len(text) // 4)
