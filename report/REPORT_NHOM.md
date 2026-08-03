# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [BỔ SUNG TÊN NHÓM]  
**Thành viên:** [BỔ SUNG HỌ TÊN CÁC THÀNH VIÊN]  
**Ngày:** 03/08/2026

> Báo cáo này ghi lại kết quả chạy có thể tái lập bằng `scripts/prepare_nd168_corpus.py` và `scripts/evaluate_nd168_strategies.py`. Tên nhóm và thành viên cần được bổ sung trước khi nộp.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề thực nghiệm:** Tra cứu quy định xử phạt vi phạm hành chính về trật tự, an toàn giao thông đường bộ, trừ điểm và phục hồi điểm giấy phép lái xe theo Nghị định 168/2024/NĐ-CP.

**Phạm vi cụ thể nhóm tập trung:**
> Nhóm tập trung vào mức phạt đối với người tham gia giao thông, thời hiệu xử phạt, thủ tục trừ/phục hồi điểm giấy phép lái xe và hiệu lực thi hành của Nghị định 168/2024/NĐ-CP.

> **Lý do chọn phạm vi:** Nhóm tự thu thập dữ liệu từ văn bản pháp luật công khai và chia tài liệu theo các phần logic để xây dựng corpus có thể truy vết, kiểm chứng và tái lập.

### Danh sách tài liệu (Data Inventory)

Nghị định dài được tách thành năm tài liệu logic liên tục. Cả năm tài liệu đều giữ URL nguồn, phiên bản và metadata truy vết về cùng văn bản gốc.

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Quy định chung và nguyên tắc xử phạt | [Cổng Chính phủ](https://vanban.chinhphu.vn/?classid=1&docid=212167&pageid=27160) | 03/08/2026 / 26/12/2024 | 15.337 | `category=general`, `subject_role=all` |
| 2 | Xử phạt người điều khiển và người tham gia giao thông | [Cổng Chính phủ](https://vanban.chinhphu.vn/?classid=1&docid=212167&pageid=27160) | 03/08/2026 / 26/12/2024 | 58.080 | `category=road-user-penalties`, `subject_role=driver` |
| 3 | Xử phạt phương tiện, vận tải và tổ chức liên quan | [Cổng Chính phủ](https://vanban.chinhphu.vn/?classid=1&docid=212167&pageid=27160) | 03/08/2026 / 26/12/2024 | 108.891 | `category=vehicle-organization-penalties`, `subject_role=organization` |
| 4 | Thẩm quyền, thủ tục và trừ điểm giấy phép lái xe | [Cổng Chính phủ](https://vanban.chinhphu.vn/?classid=1&docid=212167&pageid=27160) | 03/08/2026 / 26/12/2024 | 70.250 | `category=procedure-and-license-points`, `subject_role=authority` |
| 5 | Hiệu lực, chuyển tiếp và trách nhiệm thi hành | [Cổng Chính phủ](https://vanban.chinhphu.vn/?classid=1&docid=212167&pageid=27160) | 03/08/2026 / 26/12/2024 | 2.017 | `category=effective-and-transitional`, `subject_role=all` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**

- [x] Corpus chỉ chứa văn bản pháp luật công khai, không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` và `effective_date`.
- [x] Mỗi dòng trong `sources.csv` ánh xạ đúng một file Markdown.
- [x] Nội dung bắt đầu từ Điều 1, kết thúc ở Điều 55 và đã được đối chiếu với PDF ký số trên Cổng Chính phủ.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `nd168-nguoi-tham-gia` | Xác định tài liệu gốc của chunk và hỗ trợ xóa/cập nhật theo tài liệu. |
| `source_url` | URL | `https://vanban.chinhphu.vn/...` | Truy vết và kiểm chứng câu trả lời với nguồn chính thức. |
| `retrieved_at` | date | `2026-08-03` | Biết thời điểm nhóm thu thập dữ liệu. |
| `document_version` | date | `2024-12-26` | Phân biệt phiên bản văn bản dùng trong benchmark. |
| `effective_date` | date | `2025-01-01` | Hỗ trợ câu hỏi về thời điểm có hiệu lực. |
| `category` | enum/string | `procedure-and-license-points` | Tiền lọc đúng phần nội dung trước khi tính độ liên quan. |
| `subject_role` | enum/string | `driver` | Thu hẹp nội dung theo người điều khiển, tổ chức hoặc cơ quan có thẩm quyền. |
| `language` | string | `vi` | Hữu ích khi corpus có nhiều ngôn ngữ. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(chunk_size=500)` trên ba tài liệu đầu. Số liệu dưới đây là tổng số chunk; độ dài là trung bình của ba tài liệu.

| Tập tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| 3 tài liệu đầu | FixedSizeChunker (`fixed_size`) | 340 | 469,9 ký tự | Trung bình; ổn định nhưng có thể cắt giữa khoản và mức tiền. |
| 3 tài liệu đầu | SentenceChunker (`by_sentences`) | 168 | 841,2 ký tự | Khá tốt với văn xuôi, nhưng câu pháp lý dài làm chunk quá lớn. |
| 3 tài liệu đầu | RecursiveChunker (`recursive`) | 560 | 286,4 ký tự | Dễ đọc hơn nhưng một số điều kiện và chế tài bị tách rời. |

### Chiến lược của từng thành viên

**Thành viên 1 — [BỔ SUNG TÊN]**

- **Loại chiến lược:** FixedSize, `chunk_size=700`, `overlap=100`.
- **Mô tả & lý do chọn:** Kích thước cố định tạo các chunk đồng đều và overlap giảm nguy cơ mất thông tin ở biên. Chiến lược này phù hợp làm baseline vì không phụ thuộc chất lượng tiêu đề hay dấu câu của dữ liệu crawl.

**Thành viên 2 — [BỔ SUNG TÊN]**

- **Loại chiến lược:** Sentence, tối đa 5 câu/chunk.
- **Mô tả & lý do chọn:** Chia theo câu nhằm tránh cắt ngang câu trả lời. Tuy nhiên văn bản pháp luật có các câu và danh sách liệt kê rất dài, khiến kích thước chunk biến động lớn và tăng nhiễu khi truy xuất.

**Thành viên 3 — [BỔ SUNG TÊN]**

- **Loại chiến lược:** Custom — chia theo Điều, sau đó Recursive với giới hạn 1.200 ký tự.
- **Mô tả & lý do chọn:** Tiêu đề `Điều` là ranh giới ngữ nghĩa tự nhiên của nghị định. Nếu một điều quá dài, RecursiveChunker tiếp tục chia nhỏ để tránh vượt quá cửa sổ ngữ cảnh.
- **Code snippet:**

```python
class ArticleChunker:
    def __init__(self, chunk_size=1200):
        self.fallback = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text):
        articles = re.split(r"(?=\n#### Điều\s+\d+)", text)
        return [
            chunk
            for article in articles if article.strip()
            for chunk in self.fallback.chunk(article.strip())
        ]
```

### So Sánh Giữa Các Thành Viên

Benchmark dùng bộ xếp hạng từ khóa có trọng số theo tần suất tài liệu để kết quả tái lập mà không phụ thuộc API bên ngoài. Đây là phép đo chẩn đoán; khi nộp chính thức nên chạy lại với `EMBEDDING_PROVIDER=local`.

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| [Tên 1] | FixedSize 700/100 | 6 | 427 chunk đồng đều; tìm tốt thời hiệu, phục hồi điểm và hiệu lực. | Cắt rời hành vi với mức phạt ở câu 2–3. |
| [Tên 2] | Sentence 5 câu | 4 | Chỉ 154 chunk, giữ nguyên câu. | Trung bình 1.652,6 ký tự/chunk, quá dài và nhiều nhiễu. |
| [Tên 3] | Theo Điều + Recursive | 5 | Tôn trọng cấu trúc pháp lý, 358 chunk, dễ trích dẫn theo điều. | Điều dài vẫn phải chia; thứ hạng câu 1 chỉ đạt top-2. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Trong lần chạy hiện tại, FixedSize 700/100 đạt điểm cao nhất (6/10) vì overlap giữ được các cụm ngắn như thời hiệu và thời gian phục hồi điểm. Tuy nhiên về khả năng giải thích và trích dẫn pháp lý, chia theo Điều là nền tảng hợp lý hơn; cần cải tiến bằng cách lặp lại tiêu đề Điều/khoản ở từng chunk và gắn metadata `vehicle_type` để không nhầm mức phạt giữa ô tô và mô tô.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Thời hiệu xử phạt vi phạm hành chính về giao thông đường bộ là bao lâu? | Thời hiệu xử phạt là **01 năm**. | Điều 4; `nd168-quy-dinh-chung`, Fixed chunk 14. |
| 2 | Người lái ô tô không chấp hành đèn tín hiệu giao thông bị phạt bao nhiêu? | Phạt từ **18.000.000 đến 20.000.000 đồng**. | Điểm b khoản 9 Điều 6; `nd168-nguoi-tham-gia`. |
| 3 | Người lái xe mô tô vượt đèn đỏ bị phạt bao nhiêu tiền? | Phạt từ **4.000.000 đến 6.000.000 đồng**. | Khoản 7 Điều 7; `nd168-nguoi-tham-gia`. |
| 4 | Sau bao lâu kể từ lần trừ điểm gần nhất giấy phép lái xe được tự động phục hồi đủ 12 điểm? | Sau **12 tháng** kể từ ngày bị trừ điểm gần nhất, nếu không bị trừ hết điểm. | Điều 51; `nd168-tham-quyen-thu-tuc`, Fixed chunk 99. |
| 5 | Nghị định có hiệu lực thi hành từ ngày nào? | Nghị định có hiệu lực từ **01/01/2025**, trừ các trường hợp riêng tại khoản 2 Điều 53. | Điều 53; `nd168-hieu-luc`, Fixed chunk 0; lọc `category=effective-and-transitional`. |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hiệu xử phạt | FixedSize | Có, top-1 | Đủ cụm “thời hiệu xử phạt” và “01 năm”. |
| 2 | Mức phạt ô tô vượt đèn đỏ | Chưa có chiến lược đạt | Không | Top-3 có nội dung về đèn tín hiệu nhưng không giữ đúng mức tiền tương ứng. |
| 3 | Mức phạt mô tô vượt đèn đỏ | Chưa có chiến lược đạt | Không | Nhiễu giữa chủ thể ô tô, mô tô và các mức phạt gần nhau. |
| 4 | Phục hồi đủ 12 điểm | FixedSize và Theo Điều | Có, top-1 | Câu hỏi chứa các thuật ngữ đặc trưng nên xếp hạng tốt. |
| 5 | Ngày hiệu lực | Cả ba chiến lược | Có, top-1 | Metadata filter chỉ giữ tài liệu hiệu lực/chuyển tiếp. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có. Ở câu 5, lọc `category=effective-and-transitional` giảm không gian tìm kiếm xuống tài liệu chứa Điều 53 và đưa câu trả lời lên top-1 ở cả ba chiến lược. Câu 2–3 cho thấy corpus còn thiếu metadata `vehicle_type=car|motorcycle`; bổ sung trường này có thể loại bỏ các mức phạt đúng về hành vi nhưng sai chủ thể.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

- Chunk nhỏ không tự động tốt hơn: Recursive tạo 560 chunk trên ba tài liệu nhưng có thể tách hành vi khỏi chế tài.
- Câu pháp lý dài khiến SentenceChunker tạo chunk trung bình 1.652,6 ký tự trong cấu hình benchmark, làm tăng nhiễu.
- Metadata theo chủ thể và loại phương tiện quan trọng ngang với chunking khi nhiều điều có cấu trúc câu gần giống nhau nhưng mức phạt khác nhau.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một corpus nhưng ranh giới chunk quyết định thông tin nào cùng xuất hiện trong context. FixedSize phù hợp với các đáp án ngắn và có overlap, còn chia theo Điều thuận lợi cho trích dẫn nhưng cần truyền tiêu đề Điều và chủ thể xuống mọi chunk con. Hai câu thất bại chứng minh điểm retrieval phải được kiểm tra bằng gold answer, không thể chỉ nhìn điểm tương đồng.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ parse văn bản thành cấu trúc `chương → điều → khoản → điểm`, thêm metadata `article_number`, `vehicle_type`, `violation_type` và lặp lại tiêu đề cha trong từng chunk. Sau đó nhóm sẽ chạy embedding đa ngữ cục bộ và kết hợp metadata pre-filter với semantic search để cải thiện độ chính xác truy xuất.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 13 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 6 / 10 |
| Thuyết trình (Demo) | 4 / 5 |
| **Tổng phần nhóm** | **32 / 40** |
