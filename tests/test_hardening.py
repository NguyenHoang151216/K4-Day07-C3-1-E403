import unittest

from src import (
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    HashingEmbedder,
    KnowledgeBaseAgent,
    RecursiveChunker,
    compute_similarity,
)


class TestInputValidation(unittest.TestCase):
    def test_fixed_chunk_size_must_be_positive(self):
        with self.assertRaises(ValueError):
            FixedSizeChunker(chunk_size=0)

    def test_overlap_must_be_smaller_than_chunk(self):
        with self.assertRaises(ValueError):
            FixedSizeChunker(chunk_size=10, overlap=10)

    def test_recursive_chunk_size_must_be_positive(self):
        with self.assertRaises(ValueError):
            RecursiveChunker(chunk_size=0)

    def test_similarity_rejects_mismatched_dimensions(self):
        with self.assertRaises(ValueError):
            compute_similarity([1.0], [1.0, 2.0])


class TestStoreHardening(unittest.TestCase):
    def setUp(self):
        self.store = EmbeddingStore(embedding_fn=HashingEmbedder())
        self.store.add_documents([
            Document("a::0", "quy định cho người bán", {"doc_id": "a", "role": "seller"}),
            Document("a::1", "thông tin đăng sản phẩm", {"doc_id": "a", "role": "seller"}),
            Document("b::0", "quyền của người mua", {"doc_id": "b", "role": "buyer"}),
        ])

    def test_top_k_zero_returns_empty(self):
        self.assertEqual(self.store.search("quy định", top_k=0), [])

    def test_filter_matches_all_fields(self):
        results = self.store.search_with_filter(
            "quy định", metadata_filter={"doc_id": "a", "role": "seller"}
        )
        self.assertTrue(results)
        self.assertTrue(all(item["metadata"]["doc_id"] == "a" for item in results))

    def test_delete_removes_all_chunks(self):
        self.assertTrue(self.store.delete_document("a"))
        self.assertEqual(self.store.get_collection_size(), 1)

    def test_non_document_is_rejected(self):
        with self.assertRaises(TypeError):
            self.store.add_documents(["not a document"])


class TestGroundedAgent(unittest.TestCase):
    def test_empty_store_refuses_answer(self):
        agent = KnowledgeBaseAgent(EmbeddingStore(), lambda prompt: "should not run")
        self.assertIn("Không tìm thấy", agent.answer("Câu hỏi"))

    def test_metadata_filter_is_used(self):
        store = EmbeddingStore(embedding_fn=HashingEmbedder())
        store.add_documents([
            Document("seller", "Nội dung chỉ cho người bán", {"customer_role": "seller"}),
            Document("buyer", "Nội dung chỉ cho người mua", {"customer_role": "buyer"}),
        ])
        agent = KnowledgeBaseAgent(store, lambda prompt: prompt)
        prompt = agent.answer(
            "Nội dung là gì?", metadata_filter={"customer_role": "seller"}
        )
        self.assertIn("chỉ cho người bán", prompt)
        self.assertNotIn("chỉ cho người mua", prompt)

    def test_hashing_embedder_is_deterministic(self):
        embedder = HashingEmbedder(dim=128)
        self.assertEqual(embedder("xin chào"), embedder("xin chào"))


if __name__ == "__main__":
    unittest.main()
