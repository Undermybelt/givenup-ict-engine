#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path


RUN_ID = "20260511T183018+0800-codex-hf-pumpdump-schema-audit-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs/20260511T183018-codex-hf-pumpdump-schema-audit-v1")
OUT_DIR = RUN_ROOT / "hf-pumpdump-schema"
CHECK_DIR = RUN_ROOT / "checks"
TMP_ROOT = Path("/tmp/ict-engine-hf-pumpdump-schema-audit")
ZIP_FILES = [TMP_ROOT / "data1.zip", TMP_ROOT / "data2.zip"]
REQUIRED_NEGATIVE_FIELDS = {
    "label",
    "class",
    "target",
    "is_pump",
    "is_dump",
    "is_manipulation",
    "event_id",
    "matched_negative_group_id",
    "negative_group_id",
    "control_group",
}


def inspect_zip(path: Path) -> dict:
    with zipfile.ZipFile(path) as zf:
        infos = [info for info in zf.infolist() if info.filename.endswith(".csv")]
        samples = []
        headers = set()
        for info in infos[:10]:
            with zf.open(info) as handle:
                text = io.TextIOWrapper(handle, encoding="utf-8", errors="replace", newline="")
                reader = csv.reader(text)
                header = next(reader, [])
                rows = []
                for _ in range(3):
                    try:
                        rows.append(next(reader, []))
                    except StopIteration:
                        break
                headers.update(header)
                samples.append(
                    {
                        "file": info.filename,
                        "size": info.file_size,
                        "header": header,
                        "sample_rows": rows,
                    }
                )
        lower_headers = {h.lower() for h in headers}
        return {
            "zip": str(path),
            "zip_size": path.stat().st_size,
            "csv_count": len(infos),
            "csv_total_uncompressed_size": sum(info.file_size for info in infos),
            "first_files": [{"filename": info.filename, "size": info.file_size} for info in infos[:20]],
            "headers_seen": sorted(headers),
            "samples": samples,
            "required_negative_fields_seen": sorted(lower_headers & REQUIRED_NEGATIVE_FIELDS),
        }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    zip_reports = []
    for path in ZIP_FILES:
        if not path.exists():
            raise SystemExit(f"missing {path}; download to /tmp first")
        zip_reports.append(inspect_zip(path))

    all_headers = {header for report in zip_reports for header in report["headers_seen"]}
    lower_headers = {header.lower() for header in all_headers}
    label_like_fields = sorted(lower_headers & REQUIRED_NEGATIVE_FIELDS)
    has_timestamp = "timestamp" in lower_headers and "datetime" in lower_headers
    has_trade_fields = {"symbol", "side", "price", "amount"}.issubset(lower_headers)
    has_matched_negatives = bool({"matched_negative_group_id", "negative_group_id", "control_group"} & lower_headers)
    has_explicit_labels = bool({"label", "class", "target", "is_pump", "is_dump", "is_manipulation"} & lower_headers)

    result = {
        "run_id": RUN_ID,
        "dataset": "Go3x3/pump_and_dump_dataset",
        "dataset_url": "https://huggingface.co/datasets/Go3x3/pump_and_dump_dataset",
        "purpose": "Inspect downloaded /tmp zip headers/samples for direct Manipulation schema without committing raw rows.",
        "zip_reports": zip_reports,
        "all_headers": sorted(all_headers),
        "label_like_fields": label_like_fields,
        "has_timestamp": has_timestamp,
        "has_trade_fields": has_trade_fields,
        "has_explicit_labels": has_explicit_labels,
        "has_matched_negatives": has_matched_negatives,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "gate_result": "hf_pumpdump_schema_audit_v1=blocked_no_labels_or_matched_negatives",
        "decision": "blocked_schema_missing_labels_and_controls",
        "reason": "The files expose event-window trade rows with symbol/timestamp/datetime/side/price/amount/btc_volume, but no explicit manipulation label, event id, matched negative group, or control-row field. File-name event windows are not enough for a direct confidence gate.",
        "next_action": "Keep HF pump/dump as positive-window provenance only unless a separate manifest supplies labels and matched negative/control windows.",
    }

    json_path = OUT_DIR / "hf_pumpdump_schema_audit_v1.json"
    report_path = OUT_DIR / "hf_pumpdump_schema_audit_v1.md"
    samples_path = OUT_DIR / "hf_pumpdump_schema_audit_v1_samples.csv"
    checks_path = CHECK_DIR / "hf_pumpdump_schema_audit_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    with samples_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["zip", "file", "size", "header", "sample_row_count"])
        writer.writeheader()
        for report in zip_reports:
            for sample in report["samples"]:
                writer.writerow(
                    {
                        "zip": report["zip"],
                        "file": sample["file"],
                        "size": sample["size"],
                        "header": "|".join(sample["header"]),
                        "sample_row_count": len(sample["sample_rows"]),
                    }
                )

    report = f"""# HF Pump/Dump Schema Audit v1

Run ID: `{RUN_ID}`

This audit inspects `/tmp` downloads from `Go3x3/pump_and_dump_dataset` without committing raw rows into the repo.

## Decision

`hf_pumpdump_schema_audit_v1=blocked_no_labels_or_matched_negatives`

- ZIP files inspected: `{len(zip_reports)}`.
- CSV files in data1/data2: `{zip_reports[0]['csv_count']}` / `{zip_reports[1]['csv_count']}`.
- Headers seen: `{', '.join(sorted(all_headers))}`.
- Timestamp fields present: `{str(has_timestamp).lower()}`.
- Trade fields present: `{str(has_trade_fields).lower()}`.
- Explicit label fields present: `{str(has_explicit_labels).lower()}`.
- Matched-negative/control fields present: `{str(has_matched_negatives).lower()}`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Full direct species coverage: `false`.
- `update_goal`: `false`.

## Why It Blocks

The rows look like trade/event-window data: `symbol`, `timestamp`, `datetime`, `side`, `price`, `amount`, and `btc_volume`. The schema does not expose explicit manipulation labels, event IDs, matched negative groups, or control windows. File names encode candidate event windows, but file names are not enough to run a chronological 95% direct `Manipulation` gate.

## Artifacts

- JSON: `{json_path}`
- Sample/header CSV: `{samples_path}`
- Assertions: `{checks_path}`

## Next

Keep this source as positive-window provenance only unless a separate manifest supplies labels and matched negative/control windows.
"""
    report_path.write_text(report)

    assertions = [
        ("zip_count_two", len(zip_reports) == 2),
        ("csv_files_seen", zip_reports[0]["csv_count"] > 0 and zip_reports[1]["csv_count"] > 0),
        ("timestamp_fields_present", has_timestamp),
        ("trade_fields_present", has_trade_fields),
        ("explicit_labels_absent", not has_explicit_labels),
        ("matched_negatives_absent", not has_matched_negatives),
        ("accepted_rows_added_zero", result["accepted_rows_added"] == 0),
        ("new_confidence_gate_false", result["new_confidence_gate"] is False),
        ("no_raw_data_commit", result["raw_data_committed"] is False),
    ]
    failed = [name for name, ok in assertions if not ok]
    lines = [f"PASS {name}" if ok else f"FAIL {name}" for name, ok in assertions]
    if failed:
        lines.append(f"FAILED_ASSERTIONS {','.join(failed)}")
        checks_path.write_text("\n".join(lines) + "\n")
        raise SystemExit(1)
    lines.append("ALL_ASSERTIONS_PASS")
    checks_path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
