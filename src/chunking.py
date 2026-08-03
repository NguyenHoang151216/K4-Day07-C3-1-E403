from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        sentences = re.split(r'(?<=\. )|(?<=\! )|(?<=\? )|(?<=\.\n)', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        for s in sentences:
            current_chunk.append(s)
            if len(current_chunk) >= self.max_sentences_per_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]
            
        if not remaining_separators:
            return [current_text[i:i+self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]
            
        sep = remaining_separators[0]
        next_seps = remaining_separators[1:]
        
        if sep == "":
            return [current_text[i:i+self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]
            
        splits = current_text.split(sep)
        final_chunks = []
        current_chunk = ""
        
        for s in splits:
            if current_chunk:
                test_str = current_chunk + sep + s
            else:
                test_str = s
                
            if len(test_str) <= self.chunk_size:
                current_chunk = test_str
            else:
                if current_chunk:
                    if len(current_chunk) > self.chunk_size:
                        final_chunks.extend(self._split(current_chunk, next_seps))
                    else:
                        final_chunks.append(current_chunk)
                    current_chunk = s
                else:
                    current_chunk = s
                    
        if current_chunk:
            if len(current_chunk) > self.chunk_size:
                final_chunks.extend(self._split(current_chunk, next_seps))
            else:
                final_chunks.append(current_chunk)
                
        return final_chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    dot_product = _dot(vec_a, vec_b)
    mag_a = math.sqrt(_dot(vec_a, vec_a))
    mag_b = math.sqrt(_dot(vec_b, vec_b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot_product / (mag_a * mag_b)


class ShopeePolicyChunker:
    """
    Chiến lược Custom (TUANANH): Cắt văn bản chính sách Shopee theo từng Mục (vd: "1. ", "2. ").
    """
    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        
        # Split by Clause pattern: newline followed by a number and a dot, e.g., "\n1. "
        # Regex uses positive lookahead to keep the number with the content
        parts = re.split(r'(?=\n\d+(?:\.\d+)*\. )', "\n" + text)
        
        chunks = [p.strip() for p in parts if p.strip()]
                
        return chunks if chunks else [text]

class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed = FixedSizeChunker(chunk_size=chunk_size, overlap=20).chunk(text)
        sentences = SentenceChunker(max_sentences_per_chunk=3).chunk(text)
        recursive = RecursiveChunker(chunk_size=chunk_size).chunk(text)
        shopee_policy = ShopeePolicyChunker().chunk(text)
        
        def stats(chunks: list[str]) -> dict:
            if not chunks:
                return {'count': 0, 'avg_length': 0, 'chunks': chunks}
            avg = sum(len(c) for c in chunks) / len(chunks)
            return {'count': len(chunks), 'avg_length': avg, 'chunks': chunks}
            
        return {
            'fixed_size': stats(fixed),
            'by_sentences': stats(sentences),
            'recursive': stats(recursive),
            'tuananh_shopee_policy': stats(shopee_policy)
        }
