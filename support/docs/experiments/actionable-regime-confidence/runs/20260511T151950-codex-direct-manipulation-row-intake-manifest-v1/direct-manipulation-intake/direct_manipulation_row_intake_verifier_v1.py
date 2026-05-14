#!/usr/bin/env python3
"""Fail-closed verifier for direct Manipulation row intake exports."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


REQUIRED_FIELDS = ['label', 'source_report', 'source_section', 'trade_date', 'symbol', 'venue_or_market_center', 'participant_type_code', 'participant_identifier', 'side', 'earliest_order_received_time', 'latest_order_received_time', 'order_count', 'total_order_quantity', 'activity_description', 'matched_negative_group_id', 'session_bucket', 'source_row_id']
REQUIRED_FILES = {
    "positive_rows": "positive_spoofing_layering_rows.csv",
    "matched_negative_rows": "matched_negative_normal_activity_rows.csv",
    "provenance_manifest": "provenance_manifest.json",
}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [field for field in REQUIRED_FIELDS if field not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(f"missing_required_fields in {path}: {missing}")
        return list(reader)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intake-root", required=True)
    args = parser.parse_args()
    root = Path(args.intake_root)
    paths = {name: root / filename for name, filename in REQUIRED_FILES.items()}
    missing_files = [str(path) for path in paths.values() if not path.exists()]
    if missing_files:
        print(json.dumps({"status": "blocked", "reason": "missing_required_files", "missing_files": missing_files}, indent=2))
        return 2

    positives = read_csv_rows(paths["positive_rows"])
    negatives = read_csv_rows(paths["matched_negative_rows"])
    provenance = json.loads(paths["provenance_manifest"].read_text(encoding="utf-8"))
    if not positives or not negatives:
        print(json.dumps({"status": "blocked", "reason": "empty_positive_or_negative_rows"}, indent=2))
        return 2
    positive_groups = {row["matched_negative_group_id"] for row in positives if row.get("matched_negative_group_id")}
    negative_groups = {row["matched_negative_group_id"] for row in negatives if row.get("matched_negative_group_id")}
    orphan_groups = sorted(positive_groups - negative_groups)
    if orphan_groups:
        print(json.dumps({"status": "blocked", "reason": "positive_groups_without_matched_negatives", "groups": orphan_groups[:20]}, indent=2))
        return 2
    print(json.dumps({
        "status": "schema_ready_unscored",
        "positive_rows": len(positives),
        "matched_negative_rows": len(negatives),
        "matched_group_count": len(positive_groups & negative_groups),
        "provenance_keys": sorted(provenance.keys()),
        "next": "run chronological and heldout-symbol/venue Wilson95 calibration gate"
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
