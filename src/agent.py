from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(
        self,
        question: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> str:
        if not question or not question.strip():
            raise ValueError("question must not be empty")

        results = self.store.search_with_filter(
            question,
            top_k=top_k,
            metadata_filter=metadata_filter,
        )
        if not results:
            return "Không tìm thấy thông tin phù hợp trong cơ sở tri thức."

        context_blocks = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})
            source = metadata.get("source_url") or metadata.get("source") or result.get("id", "unknown")
            context_blocks.append(
                f"[{index}] source={source}; doc_id={metadata.get('doc_id', result.get('id', 'unknown'))}; "
                f"chunk={metadata.get('chunk_index', 'n/a')}\n{result['content']}"
            )

        prompt = (
            "Bạn là trợ lý hỏi đáp sử dụng retrieval-augmented generation.\n"
            "Chỉ trả lời dựa trên NGỮ CẢNH được cung cấp. Không tự bổ sung thông tin.\n"
            "Nếu ngữ cảnh không đủ để trả lời, hãy nói rõ rằng không đủ thông tin.\n"
            "Khi đưa ra một khẳng định, hãy trích dẫn nguồn bằng ký hiệu [1], [2], ...\n\n"
            "NGỮ CẢNH:\n"
            + "\n\n".join(context_blocks)
            + f"\n\nCÂU HỎI:\n{question.strip()}\n\nTRẢ LỜI:"
        )
        return self.llm_fn(prompt)
