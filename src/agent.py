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

    def answer(self, question: str, top_k: int = 3, metadata_filter: dict | None = None) -> str:
        results = self.store.search_with_filter(question, top_k=top_k, metadata_filter=metadata_filter)
        context = "\n\n".join(
            f"[Nguồn: {result['metadata'].get('source_url', result['metadata'].get('source', 'không rõ'))}]\n"
            f"{result['content']}"
            for result in results
        )
        prompt = (
            "Answer the question using only the context below. "
            "If the context does not contain the answer, say that you do not know.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        )
        return self.llm_fn(prompt)
