from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from ingest import build_knowledge_base
from src.agent import KnowledgeBaseAgent
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    HashingEmbedder,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)

# Thư mục dữ liệu mặc định cho demo = bộ khởi động cố định của lớp K4.
# Đổi bằng biến môi trường: LAB_DATA_DIR=data/<thu-muc-cua-nhom> python3 main.py
DEFAULT_DATA_DIR = "data/k4_ecommerce"


def _select_embedder():
    """Chọn backend nhúng (mock | hashing | local | openai)."""
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "hashing").strip().lower()
    if provider == "hashing":
        return HashingEmbedder()
    if provider == "local":
        try:
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception:
            print("Local embedder không sẵn sàng; tạm dùng hashing baseline.")
            return HashingEmbedder()
    if provider == "openai":
        try:
            return OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        except Exception:
            print("OpenAI embedder không sẵn sàng; tạm dùng hashing baseline.")
            return HashingEmbedder()
    if provider == "mock":
        return _mock_embed
    print(f"Embedding provider '{provider}' không hợp lệ; tạm dùng hashing baseline.")
    return HashingEmbedder()


def demo_llm(prompt: str) -> str:
    """Dependency-free extractive generator for the manual demo.

    It deliberately copies only retrieved sentences and adds citations.  This
    is not a replacement for a generative LLM, but is a safer offline fallback
    than returning a fabricated answer.
    """
    question_match = re.search(r"CÂU HỎI:\n(.*?)\n\nTRẢ LỜI:", prompt, re.DOTALL)
    question = question_match.group(1) if question_match else ""
    query_terms = {
        token for token in re.findall(r"\w+", question.casefold(), re.UNICODE) if len(token) > 2
    }
    blocks = re.findall(
        r"\[(\d+)\] source=.*?\n(.*?)(?=\n\n\[\d+\] source=|\n\nCÂU HỎI:)",
        prompt,
        re.DOTALL,
    )
    candidates: list[tuple[int, int, str]] = []
    for citation, content in blocks:
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", content):
            sentence = sentence.strip(" #")
            if not sentence:
                continue
            sentence_terms = set(re.findall(r"\w+", sentence.casefold(), re.UNICODE))
            overlap = len(query_terms & sentence_terms)
            if overlap:
                candidates.append((overlap, int(citation), sentence))
    candidates.sort(key=lambda item: item[0], reverse=True)

    selected: list[str] = []
    seen: set[str] = set()
    for _, citation, sentence in candidates:
        normalized = sentence.casefold()
        if normalized in seen:
            continue
        selected.append(f"{sentence} [{citation}]")
        seen.add(normalized)
        if len(selected) == 3:
            break
    if not selected:
        return "Không đủ thông tin trong ngữ cảnh được truy xuất để trả lời câu hỏi."
    return " ".join(selected)


def run_manual_demo(question: str | None = None, data_dir: str | None = None) -> int:
    data_dir = data_dir or DEFAULT_DATA_DIR
    query = question or "Tóm tắt thông tin chính từ bộ tài liệu."

    print("=== Demo pipeline nạp dữ liệu (ingest.build_knowledge_base) ===")
    print(f"Thư mục dữ liệu: {data_dir}")
    if not Path(data_dir).exists():
        print(f"Không tìm thấy thư mục dữ liệu: {data_dir}")
        print("Thu thập tài liệu vào thư mục này (xem docs/DATA_COLLECTION.md) rồi chạy lại:")
        print("  python3 main.py")
        return 1

    embedder = _select_embedder()
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    print(f"Backend nhúng: {backend}")
    if backend == "mock embeddings fallback":
        print(
            "Lưu ý: mock chỉ để chạy thử/unit test và KHÔNG phản ánh chất lượng ngữ nghĩa. "
            "Ở Giai đoạn 2, đặt EMBEDDING_PROVIDER=local để so sánh retrieval có ý nghĩa."
        )

    # Pipeline cung cấp sẵn: parse front matter -> chunk -> gắn metadata -> nạp store.
    store = build_knowledge_base(data_dir, embedding_fn=embedder)
    print(f"Đã nạp {store.get_collection_size()} chunk vào EmbeddingStore")

    print("\n=== Tìm kiếm (EmbeddingStore.search) ===")
    print(f"Câu hỏi: {query}")
    for index, result in enumerate(store.search(query, top_k=3), start=1):
        print(f"{index}. score={result['score']:.3f} source={result['metadata'].get('source')}")
        print(f"   {result['content'][:120].replace(chr(10), ' ')}...")

    print("\n=== KnowledgeBaseAgent ===")
    agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)
    print(agent.answer(query, top_k=3))
    return 0


def main() -> int:
    question = " ".join(sys.argv[1:]).strip() or None
    data_dir = os.getenv("LAB_DATA_DIR", DEFAULT_DATA_DIR)
    return run_manual_demo(question=question, data_dir=data_dir)


if __name__ == "__main__":
    raise SystemExit(main())
