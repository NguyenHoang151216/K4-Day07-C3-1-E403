#!/usr/bin/env python3
"""Extract a public Vietnamese legal PDF into a retrieval-ready Markdown file."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import fitz


def clean_page_text(text: str) -> str:
    text = text.replace("\u00ad", "").replace("\xa0", " ")
    text = re.sub(r"(?m)^\s*\d+\s*$", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def structure_legal_text(text: str) -> str:
    text = re.sub(r"(?m)^(Chương\s+[IVXLCDM]+\b.*)$", r"## \1", text)
    text = re.sub(r"(?m)^(Mục\s+\d+\b.*)$", r"### \1", text)
    text = re.sub(r"(?m)^(Điều\s+\d+[a-zA-Z]?\..*)$", r"#### \1", text)
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_pdf", type=Path)
    parser.add_argument("output_md", type=Path)
    args = parser.parse_args()

    doc = fitz.open(args.input_pdf)
    pages = [clean_page_text(page.get_text("text", sort=True)) for page in doc]
    content = structure_legal_text("\n\n".join(page for page in pages if page))
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
---

# Nghị định 168/2024/NĐ-CP

"""
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(front_matter + content + "\n", encoding="utf-8")
    print(f"pages={doc.page_count} characters={len(content)} output={args.output_md}")


if __name__ == "__main__":
    main()
