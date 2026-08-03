# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** Phạm Tuấn Anh
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**

> *1 câu — ví dụ: đổi trả + điều kiện người bán.*

### Danh sách tài liệu (Data Inventory)

| #                                                                                                                            | Tên tài liệu                            | Nguồn (Source URL)            | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán                                               |
| ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ | ------------------------------ | ------------------------ | ----------- | ---------------------------------------------------------------- |
| 1                                                                                                                            | Điều 1. Phạm vi điều chỉnh           | https://thuvienphapluat.vn/... | 2026-08-03               | ~300        | `document_version: 168/2024/NĐ-CP`, `category: traffic_law` |
| 2                                                                                                                            | Điều 2. Đối tượng áp dụng          | https://thuvienphapluat.vn/... | 2026-08-03               | ~400        | `document_version: 168/2024/NĐ-CP`, `category: traffic_law` |
| 3                                                                                                                            | Điều 3. Giải thích từ ngữ            | https://thuvienphapluat.vn/... | 2026-08-03               | ~1500       | `document_version: 168/2024/NĐ-CP`, `category: traffic_law` |
| 4                                                                                                                            | Điều 4. Hình thức xử phạt            | https://thuvienphapluat.vn/... | 2026-08-03               | ~800        | `document_version: 168/2024/NĐ-CP`, `category: traffic_law` |
| 5                                                                                                                            | Điều 5. Vi phạm quy tắc giao thông... | https://thuvienphapluat.vn/... | 2026-08-03               | ~2000       | `document_version: 168/2024/NĐ-CP`, `category: traffic_law` |
| *(Ghi chú: Bộ dữ liệu thực tế gồm 55 file Markdown từ Điều 1 đến Điều 55 của Nghị định 168/2024/NĐ-CP)* |                                            |                                |                          |             |                                                                  |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**

- [ ] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [ ] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
| ----------------- | ----- | ----------------- | ---------------------------------------------- |
|                   |       |                   |                                                |
|                   |       |                   |                                                |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu          | Chiến lược (Strategy)           | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không?                                                                    |
| ------------------- | ---------------------------------- | ----------------- | --------------------- | -------------------------------------------------------------------------------------------------- |
| art_5.md (Điều 5) | FixedSizeChunker (`fixed_size`)  | 27                | 198.74 chars          | Kém, hay bị cắt đứt đoạn giữa câu.                                                        |
| art_5.md (Điều 5) | SentenceChunker (`by_sentences`) | 8                 | 604.88 chars          | Tốt hơn, nhưng các câu trong cùng một "Khoản" có thể bị chia cắt.                      |
| art_5.md (Điều 5) | RecursiveChunker (`recursive`)   | 30                | 160.57 chars          | Đảm bảo kích thước đồng đều nhưng số lượng chunk quá lớn, rủi ro mất ngữ cảnh. |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — TUẤN ANH**

- **Loại chiến lược:** Custom (`LawClauseChunker`)
- **Mô tả & lý do chọn cho chủ đề này:** Em chọn cắt theo từng Khoản (ví dụ `1.`, `2.`) bằng Regex vì văn bản pháp luật (như Nghị định 168) có cấu trúc phân cấp rất chặt chẽ. Việc nhóm toàn bộ nội dung của một Khoản vào chung một chunk sẽ đảm bảo LLM không bị nhầm lẫn mức phạt hay đối tượng áp dụng (Context retention cực cao).
- **Code snippet (nếu custom):**

```python
class LawClauseChunker:
    def chunk(self, text: str) -> list[str]:
        if not text: return []
        parts = re.split(r'(?=\n\d+\. )', "\n" + text)
        chunks = [p.strip() for p in parts if p.strip()]
        return chunks if chunks else [text]
```

**Thành viên 2 — [Tên]**

- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**

- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
| ------------ | ------------------------ | ----------------------- | ------------ | ----------- |
|              |                          |                         |              |             |
|              |                          |                         |              |             |
|              |                          |                         |              |             |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query)                                                                                           | Câu trả lời chuẩn (Gold Answer)                                              | Chunk nào chứa thông tin? |
| - | ----------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | ---------------------------- |
| 1 | Hành vi điều khiển xe chạy quá tốc độ quy định bị phạt bao nhiêu tiền?                       | (Cần tra cứu cụ thể theo từng mức quá tốc độ trong Điều 5, Điều 6) | art_5.md / art_6.md          |
| 2 | Người đi bộ vượt đèn đỏ bị phạt bao nhiêu?                                                     | Phạt tiền từ 60.000 đồng đến 100.000 đồng.                              | art_9.md                     |
| 3 | (Dùng bộ lọc`category: traffic_law`) Thẩm quyền lập biên bản vi phạm hành chính thuộc về ai? | Cảnh sát giao thông, Cảnh sát cơ động, Thanh tra giao thông...          | art_45.md                    |
| 4 | (Dùng bộ lọc`category: traffic_law`) Hình thức xử phạt bổ sung bao gồm những gì?               | Tịch thu phương tiện, tước quyền sử dụng giấy phép lái xe...         | art_4.md                     |
| 5 | Xe máy điện chở quá số người quy định bị phạt như thế nào?                                   | (Tra cứu Điều 6)                                                              | art_6.md                     |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
| - | --------- | -------------------------------------- | --------------------------------- | -------- |
| 1 |           |                                        |                                   |          |
| 2 |           |                                        |                                   |          |
| 3 |           |                                        |                                   |          |
| 4 |           |                                        |                                   |          |
| 5 |           |                                        |                                   |          |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**

> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí                                   | Điểm tự đánh giá |
| -------------------------------------------- | ---------------------- |
| Lựa chọn tài liệu (Document Set Quality) | / 10                   |
| Thiết kế chiến lược (Strategy Design)   | / 15                   |
| Chất lượng truy xuất (Retrieval Quality) | / 10                   |
| Thuyết trình (Demo)                        | / 5                    |
| **Tổng phần nhóm**                  | **/ 40**         |
