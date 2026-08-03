# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Nguyễn Chí Hoàng]
**Nhóm:** [C3-1]
**Ngày:** 03/08/2026

## 1. Khởi động — 5 điểm

Cosine similarity đo góc giữa hai vector. Điểm gần 1 nghĩa là hai vector cùng hướng, gần 0 là ít liên hệ theo biểu diễn, và gần -1 là ngược hướng. So với Euclidean distance, cosine ít bị ảnh hưởng bởi độ lớn vector nên phù hợp khi hướng vector mang ý nghĩa chính.

- Ví dụ cao: “bảo vệ dữ liệu cá nhân” và “quy định bảo vệ dữ liệu cá nhân”; hai câu chia sẻ chủ đề và các đặc trưng chính.
- Ví dụ thấp: “quyền người tiêu dùng” và “cách nấu phở bò”; hai câu khác chủ đề.

Với tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`, bước nhảy là 450:

`ceil((10000 - 500) / 450) + 1 = 23 chunks`.

Khi overlap tăng lên 100, bước nhảy còn 400 và số chunk là:

`ceil((10000 - 500) / 400) + 1 = 25 chunks`.

Overlap lớn hơn giảm nguy cơ mất thông tin ở biên nhưng tăng số vector, chi phí tìm kiếm và kết quả gần trùng.

## 2. Hướng tiếp cận — 10 điểm

### Chunking

`SentenceChunker` dùng regex tách sau `.`, `!`, `?` hoặc xuống dòng, giữ dấu câu và loại đoạn rỗng. Các câu được gom theo `max_sentences_per_chunk`.

`RecursiveChunker` thử separator theo thứ tự đoạn văn, dòng, câu, từ và ký tự. Base case là đoạn đã không vượt `chunk_size`; khi hết separator, thuật toán cắt theo ký tự để bảo đảm kết thúc. Separator được gắn lại để hạn chế thay đổi nội dung nguồn.

`FixedSizeChunker` kiểm tra `chunk_size > 0`, `overlap >= 0` và `overlap < chunk_size` để tránh vòng lặp hoặc cấu hình vô nghĩa.

### EmbeddingStore

Mỗi record lưu `id`, `content`, bản sao `metadata`, vector và chỉ số chèn. `search` nhúng query, tính cosine với từng record, sắp giảm dần và lấy top-k. In-memory backend là contract mặc định để test tái lập.

`search_with_filter` lọc metadata trước khi tính similarity, giảm candidate và tránh lộ context sai đối tượng. `delete_document` xóa mọi chunk có cùng `metadata.doc_id`.

### KnowledgeBaseAgent

Agent retrieve top-k, tạo context block có `source`, `doc_id`, `chunk_index`, sau đó yêu cầu generator chỉ dùng bằng chứng và gắn citation `[n]`. Store rỗng được xử lý bằng câu trả lời từ chối; `metadata_filter` được truyền trực tiếp vào retrieval.

`main.py` có offline extractive generator để demo không cần API. Generator chỉ chọn câu từ context, không tự sáng tác. Với production cần thay bằng LLM thật và tiếp tục giữ prompt grounding/citation.

## 3. Hoàn thiện code — 30 điểm

Kết quả chạy trong virtual environment:

```text
platform win32 -- Python 3.14.0, pytest-9.1.1
collected 53 items
..................................................... [100%]
53 passed in 0.06s
```

Trong đó gồm **42/42 test bắt buộc** và **11 test hardening** cho validation, filter nhiều trường, xóa nhiều chunk, store rỗng và hashing embedder.

## 4. Dự đoán độ tương tự — 5 điểm

Các điểm dưới đây dùng `HashingEmbedder(512)`, vì vậy phản ánh trùng khớp từ/cặp từ, không phải mức tương đồng ngữ nghĩa của mô hình transformer.

| # | Câu A | Câu B | Dự đoán | Điểm |
|---|---|---|---|---:|
| 1 | bảo vệ dữ liệu cá nhân | quy định bảo vệ dữ liệu cá nhân | cao | 0.8563 |
| 2 | nền tảng số trung gian | trách nhiệm của nền tảng số trung gian | cao | 0.7746 |
| 3 | thương lượng khiếu nại | thời hạn thương lượng khiếu nại | cao | 0.7977 |
| 4 | quyền người tiêu dùng | cách nấu phở bò | thấp | 0.0000 |
| 5 | mua sắm xuyên biên giới | nền tảng xuyên biên giới chưa đăng ký | trung bình | 0.4303 |

Điểm đáng chú ý là các câu đồng nghĩa nhưng không dùng chung từ có thể nhận điểm thấp. Đây là giới hạn của hashing lexical và là lý do nên chạy lại benchmark bằng multilingual embedding trước khi đưa hệ thống vào thực tế.

## 5. Kết quả truy xuất cá nhân — 10 điểm

Cấu hình: `HashingEmbedder(512)`, FixedSizeChunker 500 ký tự, overlap 50, top-k=3.

| # | Top-1 document | Score | Evidence rank | Kết quả |
|---|---|---:|---:|---|
| 1 | `ecommerce-law-2025` | 0.465109 | 1 | đủ ngày hiệu lực, số chương và điều |
| 2 | `ecommerce-decree-248-2026` | 0.392618 | 1 | đủ ngày ban hành và hiệu lực |
| 3 | `consumer-rights-2023` | 0.512316 | 1 | đủ hai quyền mới |
| 4 | `platform-responsibilities` | 0.392643 | 2 | cần thêm chunk thứ hai để đủ chi tiết |
| 5 | `consumer-negotiation-and-data` | 0.192411 | 2 | cần hai chunk để tổng hợp mốc 7 và 5 ngày |

Kết quả: **5/5 query có đủ evidence trong top-3**, Hit@1 60%, Hit@3 100%, MRR 0.800, retrieval score 8/10. Offline generator tạo câu trả lời trích xuất có citation; kết quả chi tiết nằm trong `evaluation/results_hashing_fixed.md`.

Bài học quan trọng nhất là phải đánh giá evidence ở mức chunk thay vì chỉ kiểm tra document ID. Ngoài ra, metadata filter cải thiện precision rõ rệt cho câu hỏi chỉ dành cho buyer/seller.

## Tự đánh giá đề xuất

| Tiêu chí | Điểm |
|---|---:|
| Khởi động | 5/5 |
| Hướng tiếp cận | 10/10 |
| Core implementation | 30/30 |
| Similarity predictions | 5/5 |
| Retrieval | 8/10 |
| **Tổng** | **58/60** |
