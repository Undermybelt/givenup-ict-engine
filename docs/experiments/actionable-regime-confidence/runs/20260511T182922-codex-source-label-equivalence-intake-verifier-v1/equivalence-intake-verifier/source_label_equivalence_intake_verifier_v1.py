#!/usr/bin/env python3
"""Fail-closed verifier for Board A source-label equivalence intake rows."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


REQUIRED_FIELDS = ['package_id', 'source_owner', 'source_report_or_dataset', 'source_pull_date', 'market_family', 'symbol', 'source_symbol', 'equivalence_policy', 'event_species', 'timestamp_or_date', 'timeframe', 'main_regime_v2_label', 'direct_label', 'matched_negative_group_id', 'split_role', 'source_row_id', 'provenance_hash']
OPTIONAL_FIELDS = ['redaction_notes']
ROOT_LABELS = ['Bear', 'Bull', 'Crisis', 'Sideways']
DIRECT_LABELS = ['normal_control', 'positive']
PRICE_PACKAGES = ['native_subhour_overlap_after_recency', 'price_root_equivalence_crypto', 'price_root_equivalence_fx_rates_commodities', 'price_root_equivalence_us_index_futures']
DIRECT_PACKAGES = ['direct_manipulation_species_exports']
UNSUPPORTED_POLICY_TOKENS = ('ohlcv_proxy', 'generated_label', 'future_return', 'unapproved_ixic')
REQUIRED_FILES = {
    "rows": "source_label_equivalence_rows.csv",
    "provenance": "source_label_equivalence_provenance.json",
}


def blocked(reason: str, **extra: object) -> int:
    payload = {"status": "blocked", "reason": reason}
    payload.update(extra)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intake-root", required=True)
    args = parser.parse_args()
    root = Path(args.intake_root)
    rows_path = root / REQUIRED_FILES["rows"]
    provenance_path = root / REQUIRED_FILES["provenance"]
    missing = [str(path) for path in [rows_path, provenance_path] if not path.exists()]
    if missing:
        return blocked("missing_required_files", missing_files=missing)

    try:
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return blocked("provenance_json_unreadable", error=type(exc).__name__)
    with rows_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        missing_fields = [field for field in REQUIRED_FIELDS if field not in fields]
        if missing_fields:
            return blocked("missing_required_columns", missing_fields=missing_fields)
        rows = list(reader)
    if not rows:
        return blocked("empty_rows")

    bad_rows = []
    direct_groups = defaultdict(set)
    package_counts = defaultdict(int)
    split_roles = set()
    for idx, row in enumerate(rows, start=2):
        package = row.get("package_id", "")
        package_counts[package] += 1
        split_roles.add(row.get("split_role", ""))
        policy = row.get("equivalence_policy", "").lower()
        if any(token in policy for token in UNSUPPORTED_POLICY_TOKENS):
            bad_rows.append({"line": idx, "reason": "unsupported_policy_token", "package_id": package})
        if package in PRICE_PACKAGES:
            if row.get("main_regime_v2_label") not in ROOT_LABELS:
                bad_rows.append({"line": idx, "reason": "bad_main_regime_v2_label", "package_id": package})
            if not row.get("equivalence_policy"):
                bad_rows.append({"line": idx, "reason": "missing_equivalence_policy", "package_id": package})
            if row.get("direct_label") and row.get("direct_label") not in DIRECT_LABELS:
                bad_rows.append({"line": idx, "reason": "bad_direct_label", "package_id": package})
        elif package in DIRECT_PACKAGES:
            if row.get("direct_label") not in DIRECT_LABELS:
                bad_rows.append({"line": idx, "reason": "bad_direct_label", "package_id": package})
            group = row.get("matched_negative_group_id", "")
            if not group:
                bad_rows.append({"line": idx, "reason": "missing_matched_negative_group_id", "package_id": package})
            direct_groups[group].add(row.get("direct_label", ""))
        else:
            bad_rows.append({"line": idx, "reason": "unknown_package_id", "package_id": package})
    bad_groups = [
        group for group, labels in direct_groups.items()
        if "positive" in labels and "normal_control" not in labels
    ]
    if bad_rows or bad_groups:
        return blocked(
            "rows_failed_guardrails",
            bad_rows=bad_rows[:25],
            bad_direct_groups=bad_groups[:25],
        )
    required_split_present = bool({"calibration", "heldout_time", "heldout_market", "test"} & split_roles)
    if not required_split_present:
        return blocked("missing_calibration_or_heldout_split_roles", split_roles=sorted(split_roles))
    print(json.dumps({
        "status": "schema_ready_unscored",
        "row_count": len(rows),
        "package_counts": dict(sorted(package_counts.items())),
        "provenance_keys": sorted(provenance.keys()),
        "next": "rerun unchanged chronological and heldout-market/timeframe gates; do not treat schema readiness as confidence acceptance",
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
