#!/usr/bin/env python3
"""Merge indexed page lines into a clean retrieval-ready legal document."""

from __future__ import annotations

import re
from pathlib import Path


RAW_GLOB = "nghi-dinh-168-indexed-*.txt"
OUTPUT = Path("data/nghi-dinh-168/nghi-dinh-168-2024-nd-cp.md")


def main() -> None:
    indexed: dict[int, str] = {}
    for path in Path("tmp/pdfs").glob(RAW_GLOB):
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^\[L(\d+)\]\s?(.*)$", raw_line)
            if match:
                indexed[int(match.group(1))] = match.group(2)

    missing = [number for number in range(114, 578) if number not in indexed]
    if missing:
        raise ValueError(f"Missing indexed source lines: {missing}")

    content = "\n\n".join(indexed[number] for number in range(114, 578))
    content = re.sub(r"cite\d+†(.*?)", r"\1", content)
    content = re.sub(r"\s+", " ", content).strip()
    content = re.sub(r"\s+(Chương\s+[IVXLCDM]+)\s+", r"\n\n## \1\n\n", content)
    content = re.sub(r"\s+(Mục\s+\d+)\s+", r"\n\n### \1\n\n", content)
    content = re.sub(r"\s+(Điều\s+\d+[a-zA-Z]?\.[^\n]*?)(?=\s+\d+\.|\s+[A-ZÀ-Ỹ])", r"\n\n#### \1\n\n", content)

    front_matter = """---
doc_id: "nghi-dinh-168-2024-nd-cp"
title: "Nghị định 168/2024/NĐ-CP về xử phạt vi phạm hành chính trong lĩnh vực giao thông đường bộ"
source_url: "https://vanban.chinhphu.vn/?classid=1&docid=212167&pageid=27160"
source_file_url: "https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/01/168-nd-cp.signed.pdf"
reference_url: "https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Nghi-dinh-168-2024-ND-CP-xu-phat-vi-pham-hanh-chinh-an-toan-giao-thong-duong-bo-619502.aspx"
retrieved_at: "2026-08-03"
document_version: "2024-12-26"
effective_date: "2025-01-01"
issuer: "Chính phủ"
signer: "Trần Hồng Hà"
customer_role: "both"
category: "traffic-law"
language: "vi"
extraction_method: "indexed-public-page-verified-against-official-signed-pdf"
---

# Nghị định 168/2024/NĐ-CP

"""
    OUTPUT.write_text(front_matter + content + "\n", encoding="utf-8")
    print(f"lines=464 characters={len(content)} output={OUTPUT}")


if __name__ == "__main__":
    main()
