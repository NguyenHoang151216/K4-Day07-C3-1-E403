"""Validate K4 front matter and source manifest before benchmarking."""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingest import load_documents


REQUIRED_FIELDS = {
    "doc_id", "title", "source_url", "retrieved_at", "document_version", "customer_role"
}
ALLOWED_ROLES = {"buyer", "seller", "both"}


def validate(data_dir: Path) -> list[str]:
    errors: list[str] = []
    documents = load_documents(data_dir)
    manifest_path = data_dir / "sources.csv"
    manifest_ids: set[str] = set()
    if not manifest_path.is_file():
        errors.append("missing sources.csv")
    else:
        with manifest_path.open(encoding="utf-8", newline="") as source:
            manifest_ids = {row.get("doc_id", "") for row in csv.DictReader(source)}

    seen: set[str] = set()
    for doc in documents:
        source = doc.metadata.get("source", doc.id)
        missing = REQUIRED_FIELDS - doc.metadata.keys()
        if missing:
            errors.append(f"{source}: missing fields {sorted(missing)}")
        if doc.id in seen:
            errors.append(f"{source}: duplicate doc_id {doc.id}")
        seen.add(doc.id)
        if doc.metadata.get("customer_role") not in ALLOWED_ROLES:
            errors.append(f"{source}: invalid customer_role")
        try:
            date.fromisoformat(str(doc.metadata.get("retrieved_at")))
        except ValueError:
            errors.append(f"{source}: retrieved_at must use YYYY-MM-DD")
        if not str(doc.metadata.get("source_url", "")).startswith(("http://", "https://")):
            errors.append(f"{source}: source_url must be an HTTP(S) URL")
        if len(doc.content.strip()) < 100:
            errors.append(f"{source}: content is too short")

    if not 5 <= len(documents) <= 10:
        errors.append(f"expected 5-10 documents, found {len(documents)}")
    missing_manifest = seen - manifest_ids
    extra_manifest = manifest_ids - seen
    if missing_manifest:
        errors.append(f"documents missing from manifest: {sorted(missing_manifest)}")
    if extra_manifest:
        errors.append(f"manifest entries without documents: {sorted(extra_manifest)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", nargs="?", type=Path, default=Path("data/k4_ecommerce"))
    args = parser.parse_args()
    errors = validate(args.data_dir)
    if errors:
        print("Corpus KHÔNG hợp lệ:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Corpus hợp lệ: {len(load_documents(args.data_dir))} tài liệu, metadata và manifest khớp.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
