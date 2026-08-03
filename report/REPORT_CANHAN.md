# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phan Đức Anh

**Nhóm:** C3-1

**Ngày:** 03/08/2026

> Báo cáo sử dụng kết quả chạy trực tiếp từ mã nguồn trong `src`, bộ kiểm thử trong `tests` và benchmark chung trong `REPORT_NHOM.md`.

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao nghĩa là gì?**

Hai đoạn văn có cosine similarity cao khi các vector biểu diễn của chúng hướng gần giống nhau. Điều này thường cho thấy hai đoạn có nội dung hoặc ý nghĩa liên quan, ngay cả khi cách dùng từ không hoàn toàn giống nhau.

**Ví dụ có độ tương tự CAO:**

- Câu A: “Người mua có thể yêu cầu đổi trả khi sản phẩm bị lỗi.”
- Câu B: “Khách hàng được trả lại hàng nếu sản phẩm có khiếm khuyết.”
- Tại sao tương đồng: Hai câu cùng nói về quyền đổi trả của khách hàng đối với sản phẩm lỗi, chỉ khác cách diễn đạt.

**Ví dụ có độ tương tự THẤP:**

- Câu A: “Khách hàng được hoàn tiền khi hàng bị lỗi.”
- Câu B: “Thời tiết hôm nay có nhiều mây và mưa.”
- Tại sao khác: Hai câu thuộc hai chủ đề không liên quan: chính sách hoàn tiền và thời tiết.

**Tại sao cosine similarity được ưu tiên hơn khoảng cách Euclid cho text embeddings?**

Cosine tập trung vào hướng của vector nên đo được sự tương đồng về mẫu/ngữ nghĩa mà ít bị ảnh hưởng bởi độ lớn vector. Khoảng cách Euclid phụ thuộc nhiều vào độ lớn, vì vậy hai vector cùng hướng nhưng khác độ dài vẫn có thể bị xem là xa nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`:**

`ceil((10.000 - 50) / (500 - 50)) = ceil(9.950 / 450) = ceil(22,11) = 23 chunks`.

**Đáp án:** 23 chunks.

**Nếu overlap tăng lên 100:**

`ceil((10.000 - 100) / (500 - 100)) = ceil(9.900 / 400) = ceil(24,75) = 25 chunks`.

Số chunk tăng từ 23 lên 25 vì bước dịch giảm từ 450 xuống 400 ký tự. Overlap lớn hơn giúp giữ ngữ cảnh ở ranh giới chunk, giảm khả năng một điều kiện và kết luận bị tách rời, nhưng làm tăng dung lượng lưu trữ và chi phí truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`:**

Tôi dùng `re.split(r"(?<=[.!?]) +|(?<=\.)\n+", text.strip())` để nhận diện ranh giới sau dấu chấm, chấm than, chấm hỏi hoặc dấu chấm trước dòng mới. Các câu rỗng và khoảng trắng thừa được loại bỏ, sau đó câu được gom theo `max_sentences_per_chunk`; chuỗi rỗng trả về danh sách rỗng.

**`RecursiveChunker.chunk` / `_split`:**

Thuật toán thử lần lượt các separator ưu tiên `\n\n`, `\n`, `. `, khoảng trắng rồi chuỗi rỗng. Trường hợp cơ sở là đoạn đã không vượt `chunk_size`; nếu hết separator hoặc gặp separator rỗng, đoạn được cắt cứng theo kích thước. Những phần còn quá dài được đưa xuống lời gọi đệ quy với separator tiếp theo.

### Lớp EmbeddingStore

**`add_documents` + `search`:**

Mỗi tài liệu được chuẩn hóa thành record gồm ID duy nhất, nội dung, bản sao metadata và embedding; `doc_id` được bổ sung nếu chưa có. Store dùng ChromaDB khi khả dụng, nếu không sẽ lưu trong danh sách bộ nhớ. Tìm kiếm nhúng câu hỏi, tính tích vô hướng với từng embedding, sắp xếp điểm giảm dần và trả tối đa `top_k` kết quả.

**`search_with_filter` + `delete_document`:**

Metadata được lọc trước khi tính độ tương đồng để tránh xếp hạng các chunk ngoài phạm vi. Khi xóa, hệ thống tìm toàn bộ record có `metadata["doc_id"]` trùng ID cần xóa; phương thức trả `True` khi có dữ liệu bị xóa và `False` nếu không tìm thấy.

### Tác tử KnowledgeBaseAgent

**`answer`:**

Agent lấy `top_k` chunk liên quan, nối nội dung các chunk thành phần `Context`, rồi thêm câu hỏi và chỉ dẫn chỉ trả lời dựa trên context. Nếu context không chứa đáp án, prompt yêu cầu mô hình nói rằng không biết, qua đó giảm câu trả lời không có căn cứ.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết Quả Kiểm Thử

Lệnh chạy: `python -m pytest tests -q`

```text
..........................................                               [100%]
42 passed, 1 warning in 0.21s
```

Cảnh báo duy nhất là `PytestCacheWarning` do Windows không tạo lại được thư mục `.pytest_cache`; cảnh báo không ảnh hưởng kết quả kiểm thử.

**Số lượng bài test vượt qua:** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Tôi dự đoán trước dựa trên nghĩa của câu, sau đó dùng `_mock_embed` và hàm `compute_similarity()` đã cài đặt để tính điểm. Backend mock là vector giả lập xác định, chỉ phù hợp kiểm thử kỹ thuật chứ không phải mô hình ngữ nghĩa.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-------|-------|---------|--------------|-------|
| 1 | Người mua có thể yêu cầu đổi trả khi sản phẩm bị lỗi. | Khách hàng được trả lại hàng nếu sản phẩm có khiếm khuyết. | Cao | -0,0171 | Không |
| 2 | Người bán phải cung cấp mô tả sản phẩm chính xác. | Thông tin đăng bán phải phản ánh đúng tình trạng của sản phẩm. | Cao | 0,0234 | Không |
| 3 | Khách hàng được hoàn tiền khi hàng bị lỗi. | Thời tiết hôm nay có nhiều mây và mưa. | Thấp | -0,0295 | Đúng |
| 4 | Thanh toán trực tuyến cần được bảo mật. | Giao dịch online phải bảo vệ thông tin thanh toán. | Cao | 0,0084 | Không |
| 5 | Đơn hàng sẽ được giao trong ba ngày. | Chính sách quyền riêng tư bảo vệ dữ liệu cá nhân. | Thấp | 0,2344 | Không |

**Kết quả bất ngờ nhất:**

Cặp 5 khác chủ đề lại có điểm cao nhất, trong khi ba cặp tương đồng về nghĩa đều gần 0. Kết quả không cho thấy embeddings ngữ nghĩa hoạt động sai mà cho thấy `_mock_embed` tạo vector gần như ngẫu nhiên từ hash văn bản; muốn đánh giá ngữ nghĩa tiếng Việt phải chạy lại bằng mô hình đa ngữ thật như `paraphrase-multilingual-MiniLM-L12-v2`.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Tôi dùng chiến lược **FixedSizeChunker (`chunk_size=700`, `overlap=100`)** trên corpus chung Nghị định 168 và bộ xếp hạng từ khóa có trọng số của nhóm. Tổng cộng tạo 427 chunk, độ dài trung bình 695,6 ký tự. Điểm dưới đây là điểm lexical của benchmark, không phải cosine chuẩn hóa.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Score | Relevant? | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|------:|:---------:|------------------------|
| 1 | Thời hiệu xử phạt vi phạm hành chính về giao thông đường bộ là bao lâu? | `nd168-quy-dinh-chung`, chunk 14; chứa “thời hiệu xử phạt” và “01 năm”. | 22,3064 | Có | Thời hiệu xử phạt là 01 năm. |
| 2 | Người lái ô tô không chấp hành đèn tín hiệu giao thông bị phạt bao nhiêu? | `nd168-nguoi-tham-gia`, chunk 82; có hành vi giao thông nhưng không giữ đúng mức phạt ô tô. | 17,9589 | Không | Không đủ căn cứ để kết luận đúng mức 18–20 triệu đồng từ context top-1. |
| 3 | Người lái xe mô tô vượt đèn đỏ bị phạt bao nhiêu tiền? | `nd168-phuong-tien-to-chuc`, chunk 16; nói về trừ điểm và Điều 14, sai chủ thể/mức phạt. | 16,9035 | Không | Không đủ căn cứ để kết luận đúng mức 4–6 triệu đồng từ context top-1. |
| 4 | Sau bao lâu kể từ lần trừ điểm gần nhất GPLX được tự động phục hồi đủ 12 điểm? | `nd168-tham-quyen-thu-tuc`, chunk 99; chứa thời hạn và thủ tục phục hồi đủ 12 điểm. | 55,7042 | Có | Sau 12 tháng kể từ lần trừ điểm gần nhất nếu chưa bị trừ hết điểm. |
| 5 | Nghị định có hiệu lực thi hành từ ngày nào? | `nd168-hieu-luc`, chunk 0; Điều 53 ghi rõ ngày có hiệu lực. | 12,0611 | Có | Có hiệu lực từ ngày 01/01/2025, trừ trường hợp riêng tại khoản 2 Điều 53. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 3 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác:**

Chia theo cấu trúc “Điều” giúp chunk dễ đọc và dễ trích dẫn hơn cắt cố định, nhưng một điều dài vẫn phải chia nhỏ và cần lặp lại tiêu đề cha trong từng chunk. Tôi cũng nhận ra metadata như `vehicle_type` và `violation_type` có thể quan trọng ngang với embedding vì giúp loại bỏ kết quả đúng hành vi nhưng sai loại phương tiện.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **58 / 60** |
