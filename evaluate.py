"""Evaluate the three retrieval strategies on the K4 e-commerce benchmark."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ingest import build_knowledge_base
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import HashingEmbedder, LocalEmbedder, OpenAIEmbedder

ROOT = Path(__file__).resolve().parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
DATA_DIR = ROOT / "data" / "k4_ecommerce"
STRATEGIES = {
    "fixed": lambda: FixedSizeChunker(chunk_size=500, overlap=50),
    "sentence": lambda: SentenceChunker(max_sentences_per_chunk=3),
    "recursive": lambda: RecursiveChunker(chunk_size=500),
}


def make_embedder(provider: str):
    if provider == "hashing":
        return HashingEmbedder(512)
    if provider == "local":
        return LocalEmbedder()
    return OpenAIEmbedder()


def contains_evidence(results: list[dict], required_terms: list[str]) -> bool:
    evidence = " ".join(item["content"].lower() for item in results)
    return all(term.lower() in evidence for term in required_terms)


def evaluate(provider: str, strategy: str) -> dict:
    benchmark = json.loads((DATA_DIR / "benchmark.json").read_text(encoding="utf-8"))
    store = build_knowledge_base(
        DATA_DIR, make_embedder(provider), STRATEGIES[strategy](), f"k4_{provider}_{strategy}"
    )
    rows = []
    reciprocal_ranks = []
    for case in benchmark:
        results = store.search_with_filter(case["query"], 3, case.get("metadata_filter"))
        rank = 0
        for end in range(1, len(results) + 1):
            if contains_evidence(results[:end], case["required_terms"]):
                rank = end
                break
        reciprocal_ranks.append(1 / rank if rank else 0)
        rows.append({"id": case["id"], "rank": rank, "results": results})
    hit1 = sum(row["rank"] == 1 for row in rows) / len(rows)
    hit3 = sum(0 < row["rank"] <= 3 for row in rows) / len(rows)
    return {
        "provider": provider,
        "strategy": strategy,
        "chunks": store.get_collection_size(),
        "hit_at_1": hit1,
        "hit_at_3": hit3,
        "mrr": sum(reciprocal_ranks) / len(reciprocal_ranks),
        "queries": rows,
    }


def render_markdown(result: dict) -> str:
    lines = [
        f"# Kết quả retrieval: {result['provider']} / {result['strategy']}",
        "",
        f"- Số chunk: {result['chunks']}",
        f"- Hit@1: {result['hit_at_1']:.0%}",
        f"- Hit@3: {result['hit_at_3']:.0%}",
        f"- MRR: {result['mrr']:.3f}",
        "",
        "| Query | Evidence rank | Top-3 doc_id |",
        "|---:|---:|---|",
    ]
    for row in result["queries"]:
        doc_ids = ", ".join(item["metadata"].get("doc_id", "") for item in row["results"])
        lines.append(f"| {row['id']} | {row['rank'] or 'miss'} | {doc_ids} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["hashing", "local", "openai"], default="hashing")
    parser.add_argument("--strategy", choices=list(STRATEGIES), default="fixed")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = evaluate(args.provider, args.strategy)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        content = render_markdown(result) if output_path.suffix.lower() == ".md" else rendered + "\n"
        output_path.write_text(content, encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
