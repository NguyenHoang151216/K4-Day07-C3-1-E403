"""Validate K4 corpus metadata and its sources.csv manifest."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from ingest import load_documents

DATA_DIR = ROOT / "data" / "k4_ecommerce"
REQUIRED = {"doc_id", "customer_role", "category", "source_url", "retrieved_at", "document_version"}
ROLES = {"buyer", "seller", "both"}


def validate_corpus(data_dir: Path = DATA_DIR) -> list[str]:
    errors: list[str] = []
    documents = load_documents(data_dir)
    documents = [doc for doc in documents if doc.metadata.get("source", "").endswith((".md", ".txt"))]
    by_id = {doc.id: doc for doc in documents}
    if len(by_id) != len(documents):
        errors.append("doc_id bị trùng trong corpus")
    for doc in documents:
        missing = sorted(key for key in REQUIRED if not doc.metadata.get(key))
        if missing:
            errors.append(f"{doc.id}: thiếu metadata {', '.join(missing)}")
        if doc.metadata.get("customer_role") not in ROLES:
            errors.append(f"{doc.id}: customer_role không hợp lệ")
        if not str(doc.metadata.get("source_url", "")).startswith(("http://", "https://")):
            errors.append(f"{doc.id}: source_url không hợp lệ")

    manifest_path = data_dir / "sources.csv"
    with manifest_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    manifest_ids = {row["doc_id"] for row in rows}
    if manifest_ids != set(by_id):
        errors.append(f"manifest không khớp corpus: manifest={sorted(manifest_ids)}, corpus={sorted(by_id)}")
    for row in rows:
        path = ROOT / row["file_path"]
        if not path.is_file():
            errors.append(f"manifest trỏ tới file không tồn tại: {row['file_path']}")
        doc = by_id.get(row["doc_id"])
        if doc and row["source_url"] != str(doc.metadata.get("source_url")):
            errors.append(f"{doc.id}: source_url khác manifest")
    return errors


def main() -> int:
    errors = validate_corpus()
    if errors:
        print("Corpus không hợp lệ:")
        for error in errors:
            print(f"- {error}")
        return 1
    count = len(load_documents(DATA_DIR))
    print(f"OK: {count} tài liệu hợp lệ, metadata và manifest khớp.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
