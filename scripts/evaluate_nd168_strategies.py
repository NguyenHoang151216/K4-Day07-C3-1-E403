#!/usr/bin/env python3
"""Reproducible lexical retrieval benchmark for the Nghị định 168 corpus."""

from __future__ import annotations

import json
import math
import re
from collections import Counter

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ingest import load_documents
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker


class ArticleChunker:
    """Keep article boundaries, recursively splitting only oversized articles."""

    def __init__(self, chunk_size: int = 1200) -> None:
        self.fallback = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        parts = re.split(r"(?=\n#### Điều\s+\d+)", text)
        chunks: list[str] = []
        for part in parts:
            if part.strip():
                chunks.extend(self.fallback.chunk(part.strip()))
        return chunks


QUERIES = [
    {
        "id": 1,
        "query": "Thời hiệu xử phạt vi phạm hành chính về giao thông đường bộ là bao lâu?",
        "markers": ["thời hiệu xử phạt", "01 năm"],
    },
    {
        "id": 2,
        "query": "Người lái ô tô không chấp hành đèn tín hiệu giao thông bị phạt bao nhiêu?",
        "markers": ["không chấp hành hiệu lệnh của đèn tín hiệu giao thông", "18.000.000 đồng đến 20.000.000 đồng"],
    },
    {
        "id": 3,
        "query": "Người lái xe mô tô vượt đèn đỏ bị phạt bao nhiêu tiền?",
        "markers": ["không chấp hành hiệu lệnh của đèn tín hiệu giao thông", "4.000.000 đồng đến 6.000.000 đồng"],
    },
    {
        "id": 4,
        "query": "Sau bao lâu kể từ lần trừ điểm gần nhất giấy phép lái xe được tự động phục hồi đủ 12 điểm?",
        "markers": ["thời hạn 12 tháng", "tự động phục hồi đủ 12 điểm"],
    },
    {
        "id": 5,
        "query": "Nghị định có hiệu lực thi hành từ ngày nào?",
        "markers": ["có hiệu lực thi hành từ ngày 01 tháng 01 năm 2025"],
        "metadata_filter": {"category": "effective-and-transitional"},
    },
]


def tokens(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


def rank(query: str, chunks: list[dict], top_k: int = 3) -> list[dict]:
    query_terms = tokens(query)
    document_frequency = Counter()
    tokenized = []
    for chunk in chunks:
        terms = tokens(chunk["content"])
        tokenized.append(terms)
        document_frequency.update(set(terms))
    total = max(1, len(chunks))
    scored = []
    for chunk, terms in zip(chunks, tokenized):
        counts = Counter(terms)
        score = 0.0
        for term in query_terms:
            if counts[term]:
                score += (1.0 + math.log(counts[term])) * math.log((total + 1) / (document_frequency[term] + 0.5))
        scored.append({**chunk, "score": score})
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]


def main() -> None:
    docs = load_documents("data/nghi-dinh-168-corpus")
    strategies = {
        "FixedSize (700/100)": FixedSizeChunker(chunk_size=700, overlap=100),
        "Sentence (5 câu)": SentenceChunker(max_sentences_per_chunk=5),
        "Theo Điều + Recursive": ArticleChunker(chunk_size=1200),
    }
    output = {"strategies": {}, "queries": QUERIES}
    for name, chunker in strategies.items():
        chunks = []
        lengths = []
        for doc in docs:
            for index, content in enumerate(chunker.chunk(doc.content)):
                chunks.append({"content": content, "doc_id": doc.id, "chunk_index": index, "metadata": doc.metadata})
                lengths.append(len(content))
        results = []
        total_score = 0
        for item in QUERIES:
            candidates = chunks
            if item.get("metadata_filter"):
                candidates = [chunk for chunk in chunks if all(chunk["metadata"].get(k) == v for k, v in item["metadata_filter"].items())]
            top = rank(item["query"], candidates)
            marker_ranks = [
                next((i for i, chunk in enumerate(top) if marker.lower() in chunk["content"].lower()), None)
                for marker in item["markers"]
            ]
            all_found = all(rank_index is not None for rank_index in marker_ranks)
            relevant_rank = max(marker_ranks) if all_found else None
            score = 2 if all_found and 0 in marker_ranks else 1 if all_found else 0
            total_score += score
            results.append({"query_id": item["id"], "score": score, "relevant_rank": None if relevant_rank is None else relevant_rank + 1, "top_doc_ids": [x["doc_id"] for x in top], "top_chunk_indices": [x["chunk_index"] for x in top]})
        output["strategies"][name] = {
            "chunk_count": len(chunks),
            "average_length": round(sum(lengths) / len(lengths), 1),
            "score": total_score,
            "results": results,
        }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
