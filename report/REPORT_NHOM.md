# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [C3-1]
**Thành viên:** [Phan Đức Anh,Nguyễn Chí Hoàng]
**Ngày:** 03/08/2026

> Phần kỹ thuật và số liệu đã được tạo từ mã nguồn trong repo. Nhóm chỉ cần bổ sung thông tin nhận diện và gán tên thành viên cho từng chiến lược trước khi nộp.

## 1. Lựa chọn tài liệu — 10 điểm

### Phạm vi

Nhóm tập trung vào khung pháp lý và hướng dẫn bảo vệ người mua/người bán khi tham gia thương mại điện tử tại Việt Nam. Corpus gồm văn bản và bài phổ biến chính thức đang có hiệu lực, với các chủ đề: Luật Thương mại điện tử, quyền người tiêu dùng, trách nhiệm nền tảng, khiếu nại, dữ liệu cá nhân và mua sắm xuyên biên giới.

### Danh sách tài liệu

| # | Tài liệu | Cơ quan nguồn | Phiên bản | Ký tự | Role/category |
|---|---|---|---|---:|---|
| 1 | Luật Thương mại điện tử 2025 | Bộ Công Thương | 122/2025/QH15, hiệu lực 01/07/2026 | 670 | both/legal-framework |
| 2 | Nghị định 248/2026/NĐ-CP | Bộ Công Thương | hiệu lực 01/07/2026 | 636 | both/legal-framework |
| 3 | Quyền người tiêu dùng trực tuyến | Bộ Công Thương | 19/2023/QH15 | 842 | buyer/consumer-rights |
| 4 | Trách nhiệm nền tảng số trung gian | Bộ Công Thương | Luật 19/2023 + NĐ 55/2024 | 805 | seller/platform-compliance |
| 5 | Thương lượng và bảo vệ thông tin | Bộ Công Thương | 19/2023/QH15 | 852 | both/complaints |
| 6 | Bảo vệ dữ liệu cá nhân | Cổng TTĐT Chính phủ | 13/2023/NĐ-CP | 506 | both/privacy |
| 7 | An toàn mua sắm xuyên biên giới | Bộ Công Thương | cập nhật đến 03/08/2026 | 699 | buyer/shopping-safety |

URL, ngày truy xuất và quyền sử dụng được quản lý tập trung trong `data/k4_ecommerce/sources.csv`. Các file là bản tóm lược có dẫn nguồn, không chứa dữ liệu cá nhân và không được mô tả là bản thay thế văn bản pháp lý gốc.

### Metadata schema

| Trường | Kiểu | Ví dụ | Vai trò retrieval |
|---|---|---|---|
| `doc_id` | string | `platform-responsibilities` | định danh, đánh giá và xóa mọi chunk của tài liệu |
| `customer_role` | enum | `buyer`, `seller`, `both` | giới hạn context đúng đối tượng |
| `category` | string | `complaints` | lọc theo ý định câu hỏi |
| `source_url` | URL | URL Bộ Công Thương | citation và kiểm chứng |
| `retrieved_at` | date | `2026-08-03` | kiểm soát độ mới |
| `document_version` | string | `19/2023/QH15...` | phân biệt phiên bản pháp lý |
| `chunk_index` | integer | `1` | truy vết đoạn evidence |

Corpus được kiểm tra bằng `python scripts/validate_corpus.py`; kết quả: **7 tài liệu hợp lệ, metadata và manifest khớp**.

## 2. Thiết kế chiến lược — 15 điểm

Baseline embedding là `HashingEmbedder(512)`: không cần tải model, xác định và có khả năng khớp từ/cặp từ. Đây là baseline lexical, không được xem là mô hình ngữ nghĩa. Với thí nghiệm chính thức có GPU/API, nhóm nên chạy lại cùng benchmark bằng local multilingual hoặc OpenAI embedding.

### So sánh chunking trên toàn corpus

| Chiến lược | Số chunk | Độ dài TB | Hit@1 | Hit@3 | MRR | Điểm retrieval |
|---|---:|---:|---:|---:|---:|---:|
| Fixed, 500 ký tự, overlap 50 | 14 | 382.9 | 60% | 100% | 0.800 | **8/10** |
| Sentence, 3 câu/chunk | 15 | 331.7 | 40% | 100% | 0.667 | 7/10 |
| Recursive, 500 ký tự | 17 | 293.1 | 40% | 100% | 0.633 | 7/10 |

Gán tên thật trước khi nộp:

- **[Thành viên 1] — Fixed:** baseline đơn giản, overlap giúp giữ bằng chứng qua biên chunk; đạt điểm cao nhất trên corpus ngắn hiện tại.
- **[Thành viên 2] — Sentence:** chunk dễ đọc, không cắt giữa câu; một số gold answer trải qua nhiều câu nên evidence không luôn đứng top-1.
- **[Thành viên 3] — Recursive:** giữ cấu trúc đoạn tốt, phù hợp khi corpus dài/hỗn hợp; corpus hiện tại ngắn nên tạo nhiều chunk nhỏ và làm evidence phân tán.

Fixed-size là lựa chọn tốt nhất cho bộ dữ liệu nhỏ hiện tại theo MRR và điểm retrieval. Tuy nhiên, đây không phải kết luận phổ quát: sentence/recursive giữ ngữ cảnh tự nhiên tốt hơn, và cần đánh giá lại khi thay bằng tài liệu pháp lý dài hoặc embedding ngữ nghĩa.

Kết quả chi tiết có tại `evaluation/results_hashing_{fixed,sentence,recursive}.md`.

## 3. Benchmark và chất lượng truy xuất — 10 điểm

| # | Query | Gold answer rút gọn | Evidence document | Filter |
|---|---|---|---|---|
| 1 | Luật TMĐT 2025 hiệu lực khi nào, bao nhiêu chương/điều? | 01/07/2026; 7 chương, 41 điều | `ecommerce-law-2025` | — |
| 2 | NĐ 248 ban hành và hiệu lực khi nào? | 30/06/2026; 01/07/2026 | `ecommerce-decree-248-2026` | — |
| 3 | Quyền mới về tiêu dùng bền vững và tranh chấp? | môi trường lành mạnh/bền vững; quyền yêu cầu/hỗ trợ thương lượng | `consumer-rights-2023` | `customer_role=buyer` |
| 4 | Nền tảng trung gian phải công khai/minh bạch gì? | đầu mối, quy chế, quảng cáo, báo cáo kiểm duyệt | `platform-responsibilities` | `customer_role=seller` |
| 5 | Thời hạn thương lượng và báo cáo? | 7 ngày làm việc; 5 ngày làm việc | `consumer-negotiation-and-data` | `category=complaints` |

Evaluator không chỉ so `doc_id`; nó tích lũy nội dung top-k và kiểm tra các cụm bằng chứng bắt buộc (`required_terms`). Nhờ vậy, đúng tài liệu nhưng sai chunk không được tính là top-1 chính xác.

Với FixedSizeChunker, cả 5/5 query có đủ evidence trong top-3. Ba query đủ evidence ngay ở top-1; câu 4 và 5 cần hai chunk nên được 1 điểm/câu theo rubric. Tổng retrieval là **8/10**. Câu trả lời của offline extractive generator được tạo trực tiếp từ top-3 và gắn citation; khi dùng LLM thật vẫn cần đối chiếu thủ công với `gold_answer`.

Metadata filter giúp loại bỏ tài liệu khác vai trò ở câu 3 và 4, đồng thời giới hạn câu 5 vào nhóm khiếu nại. Đây vừa cải thiện precision vừa giảm nguy cơ đưa hướng dẫn sai đối tượng vào prompt.

## 4. Demo và bài học — 5 điểm

Quy trình demo:

1. `python scripts/validate_corpus.py`
2. `pytest tests/ -v`
3. `python evaluate.py --provider hashing --strategy fixed`
4. `python main.py "<câu hỏi>"`

Bài học chính:

- Đánh giá theo document ID có thể tạo điểm ảo; evidence phải nằm trong chunk được truy xuất.
- Metadata là một phần của retrieval strategy, không chỉ là thông tin phụ.
- Overlap cải thiện coverage nhưng có thể đưa nhiều chunk gần trùng nhau vào top-k.
- Hashing phù hợp baseline tái lập, nhưng không hiểu từ đồng nghĩa; cần embedding đa ngữ để kết luận chất lượng ngữ nghĩa.

Nếu làm lại với dữ liệu lớn hơn, nhóm sẽ bổ sung heading-aware chunking, loại trùng overlap, threshold từ chối context yếu và kiểm thử độ mới của `document_version`.

## Tự đánh giá đề xuất

| Tiêu chí | Điểm |
|---|---:|
| Lựa chọn tài liệu | 10/10 |
| Thiết kế chiến lược | 14/15 |
| Chất lượng truy xuất | 8/10 |
| Demo | 5/5 |
| **Tổng** | **37/40** |
