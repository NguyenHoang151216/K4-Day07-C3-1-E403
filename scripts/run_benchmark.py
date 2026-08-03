import os
import sys
import yaml
import json

# Thêm thư mục gốc vào path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.chunking import LawClauseChunker, ChunkingStrategyComparator
from src.store import EmbeddingStore
from src.agent import KnowledgeBaseAgent
from src.models import Document

def read_md_with_frontmatter(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse YAML front matter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) == 3:
            try:
                metadata = yaml.safe_load(parts[1])
                text = parts[2].strip()
                return metadata, text
            except:
                return {}, content
    return {}, content

def main():
    data_dir = r"d:\VinUni\K4-Day07-C3-1-E403\data\nghidinh168"
    
    store = EmbeddingStore()
    chunker = LawClauseChunker()
    
    print("1. Đang nạp 55 file vào Embedding Store...")
    for filename in os.listdir(data_dir):
        if filename.endswith(".md"):
            filepath = os.path.join(data_dir, filename)
            metadata, text = read_md_with_frontmatter(filepath)
            
            # Chunk the text using our custom LawClauseChunker
            chunks = chunker.chunk(text)
            
            # Add to store
            docs = []
            for j, chunk_text in enumerate(chunks):
                doc_id = f"{metadata.get('doc_id', 'doc')}_chunk_{j}"
                docs.append(Document(id=doc_id, content=chunk_text, metadata=metadata))
                
            store.add_documents(docs)
            
    print(f"Hoàn thành! Kích thước kho dữ liệu: {store.get_collection_size()} chunks.")
    
    # 2. Run ChunkingStrategyComparator on one big file to get baseline stats
    print("\n2. Phân tích đường cơ sở (Baseline Analysis) trên Điều 5...")
    _, text_art_5 = read_md_with_frontmatter(os.path.join(data_dir, "art_5.md"))
    
    comparator = ChunkingStrategyComparator()
    stats = comparator.compare(text_art_5, chunk_size=200)
    
    print("Baseline Stats (Điều 5):")
    for strategy, info in stats.items():
        print(f"  - {strategy}: {info['count']} chunks, độ dài TB: {info['avg_length']:.2f} chars")

    # 3. Query tests
    queries = [
        {"q": "Hành vi điều khiển xe chạy quá tốc độ quy định bị phạt bao nhiêu tiền?", "filter": None},
        {"q": "Người đi bộ vượt đèn đỏ bị phạt bao nhiêu?", "filter": None},
        {"q": "Thẩm quyền lập biên bản vi phạm hành chính thuộc về ai?", "filter": {"category": "traffic_law"}},
        {"q": "Hình thức xử phạt bổ sung bao gồm những gì?", "filter": {"category": "traffic_law"}},
        {"q": "Xe máy điện chở quá số người quy định bị phạt như thế nào?", "filter": None},
    ]

    def mock_llm(prompt: str) -> str:
        return "[LLM giả lập] Đã đọc Context và trả lời câu hỏi."
        
    agent = KnowledgeBaseAgent(store, llm_fn=mock_llm)
    
    print("\n3. Bắt đầu trả lời 5 câu hỏi đánh giá...")
    for i, item in enumerate(queries, 1):
        print(f"\n--- Câu {i} ---")
        print(f"Hỏi: {item['q']}")
        if item['filter']:
            print(f"Bộ lọc: {item['filter']}")
            
        # Call the search manually to see the Top-1 chunk
        results = store.search_with_filter(item['q'], metadata_filter=item['filter'] or {}, top_k=3)
        if results:
            top_1_chunk = results[0]['content'][:150].replace('\n', ' ') + "..."
            print(f"Top-1 Chunk tìm được: {top_1_chunk}")
        else:
            print("Không tìm thấy Chunk nào liên quan!")
            
        # Agent answers (lưu ý: KnowledgeBaseAgent mẫu không hỗ trợ filter_metadata)
        answer = agent.answer(item['q'])
        print(f"Agent Trả lời: {answer}")

if __name__ == "__main__":
    main()
