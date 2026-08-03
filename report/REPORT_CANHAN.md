# Báo Cáo Cá Nhân — Lab 7

**Tên thành viên:** Phạm Tuấn Anh

---

## 1. Kết quả thử nghiệm cá nhân (30 điểm)

### Cấu hình thử nghiệm

- **Chiến lược Chunking sử dụng:** `ShopeePolicyChunker` (Custom Regex chia văn bản theo tiểu mục của Chính sách Shopee, vd `1. `, `4.1. `).
- **Kích thước kho dữ liệu (Số lượng Chunk):** 16 chunks.
- **Top_k:** 1

### Chi tiết kết quả 5 câu hỏi

> Dựa vào `scripts/run_benchmark.py`, em đã thử nghiệm `ShopeePolicyChunker` và mô phỏng retrieval. Do hàm search dùng `mock_embed` (chỉ so sánh độ dài/kí tự cơ bản) nên độ chính xác chưa cao 100%, nhưng đây là kết quả thực tế từ mô phỏng:

| # | Câu hỏi | Top-1 Chunk tìm được (Trích xuất) | Đánh giá (0, 1, 2) |
| - | --- | --- | --- |
| 1 | Đối tượng nào được áp dụng chính sách trả hàng hoàn tiền? | 5. QUYỀN CỦA NGƯỜI BÁN Khi nhận được yêu cầu trả hàng... | 1 |
| 2 | Trả hàng COM là gì? | 4.2. Hạn mức Người Mua hợp lệ chỉ được Trả hàng COM... | 2 |
| 3 | Người mua có bao nhiêu ngày để gửi yêu cầu trả hàng? | 10. LIÊN LẠC GIỮA NGƯỜI BÁN VÀ NGƯỜI MUA... | 0 |
| 4 | Ai phải chịu phí vận chuyển trả hàng? | 2. ĐIỀU KIỆN ÁP DỤNG 2.1. Theo các điều khoản... | 0 |
| 5 | Thời gian giải quyết yêu cầu trả hàng là bao lâu? | 11. TRANH CHẤP GIỮA NGƯỜI MUA VÀ NGƯỜI BÁN... | 0 |

**Tổng điểm Retrieval (Ước tính):** 3 / 10

**Giải thích kết quả:**
Do sử dụng `_mock_embed` dựa trên độ phân tán vector ngẫu nhiên hoặc độ dài văn bản nên việc tìm đúng chunk chứa đáp án bị lệch khá nhiều. Nếu được thay bằng mô hình embedding thật (như OpenAI `text-embedding-3-small` hoặc HuggingFace `sentence-transformers`), thì chiến lược `ShopeePolicyChunker` sẽ phát huy tối đa sức mạnh vì nó đã nhóm chính xác trọn vẹn ngữ nghĩa của một tiểu mục (điều khoản) vào chung một chunk.

---

## 2. Phần thưởng & Tùy chọn (Optional)

**Khám phá thêm:** 
- Em đã tự động hóa việc cào và bóc tách nội dung HTML động của trang web Shopee Help Center. Script `parse_shopee.py` trích xuất chuỗi JSON (`FORGE_SSR_DATA_MAP`) từ thẻ `<script>`, sau đó dùng BeautifulSoup để chuyển HTML thành Text sạch, và cuối cùng dùng Regex cắt văn bản thành 10 file tài liệu Markdown tương ứng với 10 Mục lớn của Chính sách Trả hàng.

---

## 3. Tự Đánh Giá (Phần Cá nhân)

| Tiêu chí | Điểm tự đánh giá |
| --- | --- |
| Thử nghiệm Cá nhân (Kết quả) | / 10 |
| Phân tích & Giải thích | / 20 |
| Bonus (Cào dữ liệu/Custom) | / +10 |
| **Tổng phần cá nhân** | **/ 30** |
