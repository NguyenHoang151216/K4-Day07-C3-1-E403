# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Tên sinh viên]
**Nhóm:** [Tên nhóm]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai văn bản có cùng hướng vector, tức là có chung chủ đề, chung mặt ngữ nghĩa (semantic meaning) dù độ dài hay từ vựng chi tiết có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A:
- Câu B:
- Tại sao tương đồng:

**Ví dụ có độ tương tự THẤP:**
- Câu A:
- Câu B:
- Tại sao khác:

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Bởi vì cosine similarity chỉ quan tâm đến góc (hướng) giữa hai vector chứ không quan tâm đến độ lớn (magnitude). Văn bản dài và văn bản ngắn về cùng 1 chủ đề sẽ có chung hướng nhưng khoảng cách Euclid sẽ rất xa do độ dài khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* `(10000 - 50) / (500 - 50) = 9950 / 450 = 22.11`
> *Đáp án:* 23 chunks (làm tròn lên).

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Nếu overlap = 100, số chunk = 25. Ta muốn overlap nhiều hơn để đảm bảo các câu/ý nằm ở ranh giới giữa các chunk không bị cắt đứt đoạn, giúp LLM giữ được ngữ cảnh liền mạch khi truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng Regex `re.split` với Positive Lookbehind `(?<=\. )|(?<=\! )` để tách câu nhưng vẫn giữ lại dấu chấm/phẩy. Sau đó lặp qua list câu và nối lại cho đến khi đạt `max_sentences_per_chunk`. Dùng `.strip()` để xóa khoảng trắng thừa.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Hàm đệ quy nhận vào văn bản hiện tại và list separator. Base case là khi len(text) <= chunk_size hoặc hết separator thì trả về list. Nếu không, cắt theo separator đầu tiên, nối các phần tử lại, phần nào to quá thì gọi đệ quy (recursive call) tiếp.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Cài đặt cả 2 nhánh: nếu có thư viện `chromadb` thì add/query thẳng qua API của Chroma, nếu không có thì lưu vào 1 List Python Dictionary (in-memory) rồi loop qua List, dùng hàm `_dot` tự viết để xếp hạng.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Ở in-memory, em dùng vòng lặp for lọc bằng điều kiện (metadata filter == giá trị) trước, mảng nào thỏa mãn mới đem vào `_search_records` để giảm tính toán. Xóa thì gán lại List loại bỏ doc_id.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Gọi store `search(question)` để lấy list kết quả, map rút gọn lấy nội dung (content) và `.join("\n\n")`. Đưa khối văn bản khổng lồ đó vào biến `Context:` trong f-string, rồi đẩy tới LLM.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.12.6, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\VinUni\K4-Day07-C3-1-E403
collected 42 items

tests\test_solution.py ........................................ [ 95%]
..                                                              [100%]
============================= 42 passed in 0.12s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | | | cao / thấp | | |
| 2 | | | cao / thấp | | |
| 3 | | | cao / thấp | | |
| 4 | | | cao / thấp | | |
| 5 | | | cao / thấp | | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Hành vi điều khiển xe chạy quá tốc độ quy định bị phạt bao nhiêu tiền? | "2. Phạt tiền từ 4.000.000 đồng đến 6.000.000 đồng đối với người điều khiển xe máy chuyên dùng..." | (Giả lập) | Không (vì Mock Embedder) | [LLM giả lập] Đã đọc Context và trả lời câu hỏi. |
| 2 | Người đi bộ vượt đèn đỏ bị phạt bao nhiêu? | "4. Đối với những hành vi vi phạm quy định về tải trọng..." | (Giả lập) | Không | [LLM giả lập] Đã đọc Context và trả lời câu hỏi. |
| 3 | (Dùng bộ lọc `category: traffic_law`) Thẩm quyền lập biên bản vi phạm hành chính thuộc về ai? | "2. Phạt tiền từ 400.000 đồng đến 600.000 đồng đối với một trong các hành vi vi phạm sau đây: a) Không chấp hành hiệu lệnh..." | (Giả lập) | Không | [LLM giả lập] Đã đọc Context và trả lời câu hỏi. |
| 4 | (Dùng bộ lọc `category: traffic_law`) Hình thức xử phạt bổ sung bao gồm những gì? | "1. Phạt tiền từ 1.000.000 đồng đến 2.000.000 đồng đối với hành vi chở quá số người quy định..." | (Giả lập) | Không | [LLM giả lập] Đã đọc Context và trả lời câu hỏi. |
| 5 | Xe máy điện chở quá số người quy định bị phạt như thế nào? | "2. Phạt tiền từ 2.000.000 đồng đến 3.000.000 đồng đối với hành vi điều khiển xe ô tô kinh doanh vận tải chở trẻ em..." | (Giả lập) | Không | [LLM giả lập] Đã đọc Context và trả lời câu hỏi. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 0 / 5 (Do hệ thống đang dùng hàm `_mock_embed` thay vì Text Embeddings thực sự, nên các chunk trả về chưa mang tính chính xác về mặt ngữ nghĩa).

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Nhận ra rằng nếu không có thư viện Embeddings chuẩn (như ChromaDB với mô hình AI thực thụ), thuật toán tính khoảng cách vector ngẫu nhiên hoặc hashing sẽ hoàn toàn vô dụng trong việc tìm kiếm ngữ nghĩa.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
