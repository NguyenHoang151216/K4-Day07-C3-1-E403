# Kết quả benchmark K4

- Backend: `hashing lexical embeddings (512d)`
- Chunking: `sentence` (`chunk_size=500`)
- Số chunk: 15
- Hit@1: 40.0%
- Hit@3: 100.0%
- MRR: 0.667
- Điểm retrieval: 7/10

| Query | Filter | Top-1 | Hit@3 | Gold answer |
| --- | --- | --- | --- | --- |
| Luật Thương mại điện tử 2025 có hiệu lực khi nào và gồm bao nhiêu chương, điều? | `null` | `ecommerce-law-2025` | Có | Luật số 122/2025/QH15 có hiệu lực từ ngày 01/07/2026, gồm 7 chương và 41 điều. |
| Nghị định 248/2026/NĐ-CP được ban hành ngày nào và có hiệu lực từ ngày nào? | `null` | `personal-data-protection` | Có | Nghị định được ban hành ngày 30/06/2026 và có hiệu lực từ ngày 01/07/2026. |
| Người tiêu dùng có những quyền mới nào liên quan đến tiêu dùng bền vững và giải quyết tranh chấp? | `{"customer_role": "buyer"}` | `consumer-rights-2023` | Có | Người tiêu dùng có quyền được tạo điều kiện lựa chọn môi trường tiêu dùng lành mạnh, bền vững và quyền yêu cầu tổ chức hoặc hỗ trợ thương lượng để giải quyết tranh chấp. |
| Nền tảng số trung gian phải công khai và minh bạch những nội dung gì để bảo vệ người tiêu dùng? | `{"customer_role": "seller"}` | `platform-responsibilities` | Có | Nền tảng phải công khai đầu mối làm việc với cơ quan nhà nước, công khai quy chế và phân định trách nhiệm, minh bạch quảng cáo, đồng thời cung cấp báo cáo kiểm duyệt và báo cáo theo yêu cầu. |
| Bên kinh doanh phải tiến hành thương lượng trong bao lâu và báo cáo kết quả trong bao lâu? | `{"category": "complaints"}` | `consumer-negotiation-and-data` | Có | Phải tiến hành thương lượng trong 7 ngày làm việc từ khi nhận yêu cầu và thông báo bằng văn bản kết quả trong 5 ngày làm việc từ khi kết thúc thương lượng. |

> Điểm trên chỉ đo retrieval. Cần đối chiếu câu trả lời của agent với gold answer để chấm phần generation theo rubric.

