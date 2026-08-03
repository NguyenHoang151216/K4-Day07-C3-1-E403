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
> *Chính sách Trả hàng và Hoàn tiền dành cho Người mua và Người bán trên sàn thương mại điện tử Shopee.*

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
| --- | --- | --- | --- | --- | --- |
| 1 | Mục 1. Đối tượng và Phạm vi áp dụng | https://help.shopee.vn/portal/4/article/77251 | 2026-08-03 | ~1000 | `category: returns` |
| 2 | Mục 2. Điều kiện áp dụng | https://help.shopee.vn/portal/4/article/77251 | 2026-08-03 | ~1000 | `category: returns` |
| 3 | Mục 3. Điều kiện yêu cầu trả hàng/hoàn tiền | https://help.shopee.vn/portal/4/article/77251 | 2026-08-03 | ~2000 | `category: returns` |
| 4 | Mục 4. Quy định bổ sung đối với các trường hợp trả hàng COM | https://help.shopee.vn/portal/4/article/77251 | 2026-08-03 | ~5200 | `category: returns` |
| 5 | Mục 5. Quyền của Người Bán | https://help.shopee.vn/portal/4/article/77251 | 2026-08-03 | ~1500 | `category: returns` |
| 6 | Mục 6, 7, 8, 9, 10, 11, 12... | https://help.shopee.vn/portal/4/article/77251 | 2026-08-03 | Đa dạng | `category: returns` |

*(Ghi chú: Bộ dữ liệu gồm 10 file Markdown bóc tách từ các đề mục của Chính sách Trả hàng & Hoàn tiền Shopee, lưu tại `data/shopee/`)*

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
| --- | --- | --- | --- |
| `category` | String | `returns` | Giúp lọc nhanh các tài liệu liên quan đến trả hàng thay vì tìm kiếm toàn bộ chính sách sàn. |
| `source_url` | String | `https://...` | Cung cấp nguồn gốc tài liệu để trích dẫn hoặc kiểm chứng thông tin thực tế. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 1 tài liệu lớn (Mục 4 - Quy định bổ sung Trả hàng COM):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
| --- | --- | --- | --- | --- |
| section_4.md | FixedSizeChunker (`fixed_size`) | 29 | 199.34 chars | Kém, câu bị cắt ngang giữa chừng, mất liên kết ý nghĩa. |
| section_4.md | SentenceChunker (`by_sentences`) | 16 | 325.38 chars | Khá, nhưng các ý nhỏ (như 4.1.a, 4.1.b) bị tách rời khỏi tiêu đề lớn. |
| section_4.md | RecursiveChunker (`recursive`) | 49 | 105.31 chars | Quá nhiều chunk nhỏ lẻ, khó nắm bắt ngữ cảnh toàn bộ mục. |

### Chiến lược của từng thành viên

**Thành viên 1 — TUẤN ANH**

- **Loại chiến lược:** Custom (`ShopeePolicyChunker`)
- **Mô tả & lý do chọn cho chủ đề này:** Em sử dụng Regex `(?=\n\d+(?:\.\d+)*\. )` để cắt văn bản theo từng phân mục của Shopee (ví dụ: `1. `, `4.1. `). Các chính sách của sàn TMĐT thường phân mục rất rõ ràng theo điều khoản. Nhóm toàn bộ nội dung của một tiểu mục vào cùng một chunk giúp LLM hiểu trọn vẹn quyền và nghĩa vụ của người mua/người bán trong tiểu mục đó.
- **Code snippet (nếu custom):**
```python
class ShopeePolicyChunker:
    def chunk(self, text: str) -> list[str]:
        if not text: return []
        parts = re.split(r'(?=\n\d+(?:\.\d+)*\. )', "\n" + text)
        chunks = [p.strip() for p in parts if p.strip()]
        return chunks if chunks else [text]
```

**Thành viên 2 — NGUYỄN ĐỨC ANH**
- **Loại chiến lược:** `FixedSizeChunker` (chunk_size=700, overlap=100)
- **Mô tả & lý do chọn:** Chia văn bản thành các đoạn độ dài cố định 700 ký tự, có 100 ký tự giao nhau (overlap) ở hai đầu. Lý do là để đảm bảo các đoạn không quá dài hoặc quá ngắn, và phần overlap giúp giữ lại ngữ cảnh ở các ranh giới cắt, giảm khả năng một điều kiện và kết luận bị tách rời.

**Thành viên 3 — NGUYỄN CHÍ HOÀNG**
- **Loại chiến lược:** `SentenceChunker` & `FixedSizeChunker` (chunk_size=500, overlap=50)
- **Mô tả & lý do chọn:** Chia nhỏ văn bản theo câu dựa trên dấu chấm, chấm hỏi, chấm than, sau đó mới gom các câu lại. Cách tiếp cận này giúp giữ lại trọn vẹn ngữ nghĩa của một câu hoàn chỉnh, tránh tình trạng bị cắt ngang giữa chừng một từ như FixedSizeChunker cơ bản.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
| ------------ | ------------------------ | ----------------------- | ------------ | ----------- |
| Tuấn Anh | `ShopeePolicyChunker` (Custom) | Ước tính 3/10 (mock_embed) | Giữ trọn vẹn ngữ cảnh của một điều khoản/tiểu mục. Không bao giờ bị cắt ngang ý. | Số lượng chunk ít nhưng dài, đòi hỏi LLM context window phải lớn. Dễ bị miss nếu mock_embed tính theo độ dài. |
| Đức Anh | `FixedSizeChunker` (700, 100) | 8/10 | Kích thước đồng đều, dễ tối ưu hóa hiệu suất tính toán vector. | Có thể cắt ngang một điều khoản quan trọng, dẫn tới mất liên kết thông tin. |
| Chí Hoàng | `SentenceChunker` (500, 50) | 8/10 | Giữ trọn vẹn từng câu, không cắt giữa từ. | Các câu trong cùng một đoạn đôi khi bị tách rời nếu vượt quá max_sentences. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

> *Chiến lược Custom (`ShopeePolicyChunker`) của Tuấn Anh mang ý nghĩa thiết kế tốt nhất cho văn bản chính sách (Shopee), vì nó bảo toàn hoàn hảo cấu trúc logic điều khoản. Tuy nhiên, nếu xét về mặt an toàn hiệu suất và khả năng tương thích với mọi loại Embedding Model, thì sự kết hợp của `SentenceChunker` với `overlap` (của Chí Hoàng) là phương án cân bằng nhất.*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
| - | --- | --- | --- |
| 1 | Đối tượng nào được áp dụng chính sách trả hàng hoàn tiền? | Người Mua, Người Bán, các đơn vị vận chuyển, shipper... | section_1.md |
| 2 | Trả hàng COM là gì? | Sản Phẩm ở trạng thái nguyên vẹn, nguyên bao bì nhưng Người Mua không còn nhu cầu. | section_3.md |
| 3 | (Lọc `category: returns`) Người mua có bao nhiêu ngày để gửi yêu cầu trả hàng? | 15 ngày (đối với hàng thường), 24 giờ (đối với thực phẩm tươi sống/đông lạnh). | section_3.md |
| 4 | (Lọc `category: returns`) Ai phải chịu phí vận chuyển trả hàng? | Tùy từng trường hợp, Shopee quy định cụ thể tại Mục 8 (Người mua có thể thỏa thuận với Người bán). | section_8.md |
| 5 | Thời gian giải quyết yêu cầu trả hàng là bao lâu? | Tùy thuộc vào thời điểm Người Bán phản hồi và quyết định của Shopee. | section_5.md / 6.md |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
| - | --------- | -------------------------------------- | --------------------------------- | -------- |
| 1 | Câu 1 | `SentenceChunker` | Có | Câu trả lời trải dài, cắt theo câu bắt tốt ý chính. |
| 2 | Câu 2 | `ShopeePolicyChunker` | Có | Thuật toán cắt vừa vặn trọn mục 4 nói về Trả hàng COM. |
| 3 | Câu 3 | `FixedSizeChunker` | Có | Thông tin dạng số (15 ngày) dễ bị tóm bởi chunk nhỏ cố định. |
| 4 | Câu 4 | `ShopeePolicyChunker` | Có | Thông tin về phí vận chuyển cần đọc toàn bộ bối cảnh của cả Mục 8. |
| 5 | Câu 5 | `SentenceChunker` | Có | Câu hỏi tìm thời gian giải quyết cụ thể, bắt theo câu là đủ. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

> *Có, rất hữu ích ở các câu 3 và 4. Khi áp dụng `metadata_filter: {"category": "returns"}`, hệ thống bỏ qua các chính sách chung hoặc chính sách bảo mật, giúp tập trung thẳng vào tài liệu Trả hàng/Hoàn tiền, đẩy chunk chứa kết quả lên Top 1 dễ dàng hơn.*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

> - Đặc thù của tài liệu chính sách/pháp lý là tính phân cấp cao (Điều, Khoản, Mục). Cắt ngang (FixedSize) có thể phá vỡ bối cảnh pháp lý, dẫn đến AI trả lời sai mức phạt / quyền lợi.
> - Việc sử dụng Regex để bám theo layout của chính sách (ShopeePolicyChunker) cải thiện đáng kể khả năng trả lời các câu hỏi tổng hợp.
> - Metadata Filtering là tính năng bắt buộc phải có nếu quy mô tài liệu lớn hơn 100 file.

**Bài học rút ra khi so sánh trong nhóm:**

> *Cùng một tài liệu nhưng nếu dùng FixedSizeChunker, một câu hỏi có thể trả về đáp án bị cụt ý (thiếu điều kiện loại trừ). Trong khi đó dùng Custom Chunker theo từng mục thì đảm bảo lấy được đủ cả quyền lợi và điều kiện áp dụng, dù chunk sinh ra sẽ lớn hơn đôi chút.*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

> *Nhóm sẽ bổ sung thêm các trường metadata chi tiết hơn (như `audience: buyer/seller`) để dễ dàng filter khi câu hỏi chỉ áp dụng riêng cho người bán hoặc người mua.*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
| --- | --- |
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
