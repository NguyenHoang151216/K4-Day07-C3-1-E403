#!/usr/bin/env python3
"""Split Nghị định 168 into five traceable logical documents for the lab corpus."""

from __future__ import annotations

from pathlib import Path

SOURCE = Path("data/nghi-dinh-168/nghi-dinh-168-2024-nd-cp.md")
OUTPUT = Path("data/nghi-dinh-168-corpus")
BOUNDARIES = ["Điều 1.", "Điều 6.", "Điều 13.", "Điều 36.", "Điều 53."]
DOCS = [
    ("nd168-quy-dinh-chung", "Quy định chung và nguyên tắc xử phạt", "general", "all"),
    ("nd168-nguoi-tham-gia", "Xử phạt người điều khiển và người tham gia giao thông", "road-user-penalties", "driver"),
    ("nd168-phuong-tien-to-chuc", "Xử phạt phương tiện, vận tải và tổ chức liên quan", "vehicle-organization-penalties", "organization"),
    ("nd168-tham-quyen-thu-tuc", "Thẩm quyền, thủ tục và trừ điểm giấy phép lái xe", "procedure-and-license-points", "authority"),
    ("nd168-hieu-luc", "Hiệu lực, chuyển tiếp và trách nhiệm thi hành", "effective-and-transitional", "all"),
]


def quoted(value: str) -> str:
    return '"' + value.replace('"', '\\"') + '"'


def main() -> None:
    raw = SOURCE.read_text(encoding="utf-8")
    body = raw.split("---", 2)[2].lstrip() if raw.startswith("---") else raw
    positions: list[int] = []
    cursor = 0
    for marker in BOUNDARIES:
        position = body.find(marker, cursor)
        if position < 0:
            raise ValueError(f"Cannot find boundary {marker}")
        positions.append(position)
        cursor = position + len(marker)
    positions.append(len(body))

    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows = ["doc_id,file_path,title,source_url,retrieved_at,document_version,license_or_permission"]
    for index, (doc_id, title, category, subject_role) in enumerate(DOCS):
        content = body[positions[index] : positions[index + 1]].strip()
        metadata = {
            "doc_id": doc_id,
            "title": title,
            "source_url": "https://vanban.chinhphu.vn/?classid=1&docid=212167&pageid=27160",
            "reference_url": "https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Nghi-dinh-168-2024-ND-CP-xu-phat-vi-pham-hanh-chinh-an-toan-giao-thong-duong-bo-619502.aspx",
            "retrieved_at": "2026-08-03",
            "document_version": "2024-12-26",
            "effective_date": "2025-01-01",
            "customer_role": "both",
            "category": category,
            "subject_role": subject_role,
            "language": "vi",
        }
        front = "\n".join(f"{key}: {quoted(value)}" for key, value in metadata.items())
        path = OUTPUT / f"{doc_id}.md"
        path.write_text(f"---\n{front}\n---\n\n# {title}\n\n{content}\n", encoding="utf-8")
        rows.append(",".join([doc_id, str(path).replace("\\", "/"), quoted(title), metadata["source_url"], metadata["retrieved_at"], metadata["document_version"], "official-public-record"]))
        print(doc_id, len(content))
    (OUTPUT / "sources.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
