"""Reproducible retrieval benchmark for the K4 e-commerce corpus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ingest import build_knowledge_base
from src import FixedSizeChunker, HashingEmbedder, RecursiveChunker, SentenceChunker
from src.embeddings import LocalEmbedder, MockEmbedder, OpenAIEmbedder


def load_queries(path: Path) -> list[dict]:
    queries = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(queries, list) or not queries:
        raise ValueError("benchmark file must contain a non-empty JSON list")
    required = {"id", "query", "expected_doc_ids", "required_terms", "gold_answer"}
    for item in queries:
        missing = required - item.keys()
        if missing:
            raise ValueError(f"query {item.get('id', '?')} is missing: {sorted(missing)}")
    return queries


def select_embedder(provider: str):
    if provider == "mock":
        return MockEmbedder()
    if provider == "hashing":
        return HashingEmbedder()
    if provider == "local":
        return LocalEmbedder()
    if provider == "openai":
        return OpenAIEmbedder()
    raise ValueError(f"unsupported provider: {provider}")


def select_chunker(strategy: str, chunk_size: int):
    if strategy == "fixed":
        return FixedSizeChunker(chunk_size=chunk_size, overlap=min(50, chunk_size // 5))
    if strategy == "sentence":
        return SentenceChunker(max_sentences_per_chunk=3)
    if strategy == "recursive":
        return RecursiveChunker(chunk_size=chunk_size)
    raise ValueError(f"unsupported strategy: {strategy}")


def evidence_rank(results: list[dict], expected: set[str], required_terms: list[str]) -> int | None:
    """Return the first rank where accumulated expected evidence covers the gold facts."""
    evidence = ""
    terms = [term.casefold() for term in required_terms]
    for rank, result in enumerate(results, start=1):
        doc_id = result["metadata"].get("doc_id", result["id"])
        if doc_id in expected:
            evidence += "\n" + result["content"].casefold()
        if evidence and all(term in evidence for term in terms):
            return rank
    return None


def run_benchmark(
    data_dir: Path,
    benchmark_path: Path,
    provider: str,
    strategy: str,
    chunk_size: int,
    top_k: int,
) -> dict:
    embedder = select_embedder(provider)
    chunker = select_chunker(strategy, chunk_size)
    store = build_knowledge_base(
        data_dir,
        embedding_fn=embedder,
        chunker=chunker,
        collection_name=f"k4_{provider}_{strategy}",
    )

    rows = []
    for item in load_queries(benchmark_path):
        results = store.search_with_filter(
            item["query"], top_k=top_k, metadata_filter=item.get("metadata_filter")
        )
        expected = set(item["expected_doc_ids"])
        coverage_rank = evidence_rank(results, expected, item["required_terms"])
        rr = 1.0 / coverage_rank if coverage_rank else 0.0
        rows.append({
            **item,
            "retrieved": [
                {
                    "rank": rank,
                    "doc_id": result["metadata"].get("doc_id", result["id"]),
                    "chunk_index": result["metadata"].get("chunk_index"),
                    "score": round(result["score"], 6),
                    "source_url": result["metadata"].get("source_url"),
                    "preview": result["content"][:240].replace("\n", " "),
                }
                for rank, result in enumerate(results, start=1)
            ],
            "evidence_rank": coverage_rank,
            "hit_at_1": coverage_rank == 1,
            "hit_at_3": coverage_rank is not None and coverage_rank <= 3,
            "reciprocal_rank": rr,
            # Mirrors the retrieval half of the course rubric. Agent answer
            # correctness remains a documented manual check against gold_answer.
            "retrieval_score": 2 if coverage_rank == 1 else (1 if coverage_rank and coverage_rank <= 3 else 0),
        })

    count = len(rows)
    return {
        "configuration": {
            "data_dir": str(data_dir),
            "benchmark": str(benchmark_path),
            "provider": provider,
            "backend": getattr(embedder, "_backend_name", type(embedder).__name__),
            "strategy": strategy,
            "chunk_size": chunk_size,
            "top_k": top_k,
            "collection_size": store.get_collection_size(),
        },
        "metrics": {
            "queries": count,
            "hit_at_1": sum(row["hit_at_1"] for row in rows) / count,
            "hit_at_3": sum(row["hit_at_3"] for row in rows) / count,
            "mrr": sum(row["reciprocal_rank"] for row in rows) / count,
            "retrieval_score": sum(row["retrieval_score"] for row in rows),
            "retrieval_score_max": count * 2,
        },
        "results": rows,
    }


def to_markdown(report: dict) -> str:
    config = report["configuration"]
    metrics = report["metrics"]
    lines = [
        "# Kết quả benchmark K4",
        "",
        f"- Backend: `{config['backend']}`",
        f"- Chunking: `{config['strategy']}` (`chunk_size={config['chunk_size']}`)",
        f"- Số chunk: {config['collection_size']}",
        f"- Hit@1: {metrics['hit_at_1']:.1%}",
        f"- Hit@3: {metrics['hit_at_3']:.1%}",
        f"- MRR: {metrics['mrr']:.3f}",
        f"- Điểm retrieval: {metrics['retrieval_score']}/{metrics['retrieval_score_max']}",
        "",
        "| Query | Filter | Top-1 | Hit@3 | Gold answer |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["results"]:
        top_one = row["retrieved"][0]["doc_id"] if row["retrieved"] else "—"
        lines.append(
            f"| {row['query']} | `{json.dumps(row.get('metadata_filter'), ensure_ascii=False)}` "
            f"| `{top_one}` | {'Có' if row['hit_at_3'] else 'Không'} | {row['gold_answer']} |"
        )
    lines.extend([
        "",
        "> Điểm trên chỉ đo retrieval. Cần đối chiếu câu trả lời của agent với gold answer để chấm phần generation theo rubric.",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/k4_ecommerce"))
    parser.add_argument("--benchmark", type=Path, default=Path("benchmarks/k4_queries.json"))
    parser.add_argument("--provider", choices=["hashing", "mock", "local", "openai"], default="hashing")
    parser.add_argument("--strategy", choices=["fixed", "sentence", "recursive"], default="recursive")
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true", help="write/print JSON instead of Markdown")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_benchmark(
        args.data_dir, args.benchmark, args.provider, args.strategy, args.chunk_size, args.top_k
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2) if args.json else to_markdown(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Đã ghi kết quả: {args.output}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
