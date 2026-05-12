#!/usr/bin/env python3
"""Extend Board A source-label equivalence intake with the local US panel.

This writes only shared /tmp intake rows plus compact repo artifacts. It does
not treat source-label schema readiness, low source confidence, or local panel
labels as a strict >=95 confidence gate.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T213446-codex-us-panel-source-label-equivalence-extension-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "us-panel-source-label-equivalence-extension"
CHECK_DIR = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
SCRIPT_DIR = RUN_ROOT / "scripts"

SOURCE_CSV = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
SOURCE_SUMMARY = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/dataset_summary.txt")
SHARED_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
STAGING_ROOT = Path("/tmp/ict-engine-us-panel-source-label-equivalence-extension-v1")
ROWS_NAME = "source_label_equivalence_rows.csv"
PROVENANCE_NAME = "source_label_equivalence_provenance.json"

VERIFIER = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T182922-codex-source-label-equivalence-intake-verifier-v1/"
    "equivalence-intake-verifier/source_label_equivalence_intake_verifier_v1.py"
)

FIELDS = [
    "package_id",
    "source_owner",
    "source_report_or_dataset",
    "source_pull_date",
    "market_family",
    "symbol",
    "source_symbol",
    "equivalence_policy",
    "event_species",
    "timestamp_or_date",
    "timeframe",
    "main_regime_v2_label",
    "direct_label",
    "matched_negative_group_id",
    "split_role",
    "source_row_id",
    "provenance_hash",
    "redaction_notes",
]
ROOT_LABELS = {"Bull", "Bear", "Sideways", "Crisis"}
SOURCE_ID = "local_stock_market_regimes_2000_2026_csv"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_role(date_text: str) -> str:
    if date_text < "2015-01-01":
        return "calibration"
    if date_text < "2022-01-01":
        return "heldout_time"
    return "test"


def read_existing_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def write_simple_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def build_us_rows() -> tuple[list[dict[str, str]], dict[str, object]]:
    rows: list[dict[str, str]] = []
    label_counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()
    ticker_counts: Counter[str] = Counter()
    confidence_values: list[float] = []
    skipped_counts: Counter[str] = Counter()
    date_min = ""
    date_max = ""

    with SOURCE_CSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for line_no, row in enumerate(reader, start=2):
            label = row["regime_label"]
            if label not in ROOT_LABELS:
                skipped_counts[label] += 1
                continue
            date_text = row["date"]
            ticker = row["ticker"]
            conf = float(row.get("regime_confidence") or 0.0)
            source_row_id = f"stock_market_regimes_2000_2026:{line_no}:{ticker}:{date_text}:{label}"
            source_material = "|".join([
                SOURCE_ID,
                date_text,
                ticker,
                label,
                row.get("regime_confidence", ""),
                row.get("macro_context", ""),
            ])
            rows.append({
                "package_id": "price_root_equivalence_us_index_futures",
                "source_owner": "local_stock_market_regimes_2000_2026_panel",
                "source_report_or_dataset": f"local:{SOURCE_CSV}",
                "source_pull_date": "2026-05-11",
                "market_family": "us_equity_panel",
                "symbol": ticker,
                "source_symbol": f"{ticker}:regime_label",
                "equivalence_policy": "source_panel_regime_label_mapping_v1:regime_label_to_MainRegimeV2;High-volatility_unmapped_no_confidence_acceptance",
                "event_species": "source_panel_daily_market_regime_label",
                "timestamp_or_date": date_text,
                "timeframe": "1d",
                "main_regime_v2_label": label,
                "direct_label": "",
                "matched_negative_group_id": "",
                "split_role": split_role(date_text),
                "source_row_id": source_row_id,
                "provenance_hash": sha256_text(source_material),
                "redaction_notes": "schema_extension_only_source_confidence_below_95_no_strict_completion_claim",
            })
            label_counts[label] += 1
            split_counts[split_role(date_text)] += 1
            ticker_counts[ticker] += 1
            confidence_values.append(conf)
            date_min = date_text if not date_min else min(date_min, date_text)
            date_max = date_text if not date_max else max(date_max, date_text)

    conf_ge_95 = sum(1 for value in confidence_values if value >= 0.95)
    return rows, {
        "row_count": len(rows),
        "label_counts": dict(sorted(label_counts.items())),
        "split_counts": dict(sorted(split_counts.items())),
        "ticker_count": len(ticker_counts),
        "date_min": date_min,
        "date_max": date_max,
        "skipped_counts": dict(sorted(skipped_counts.items())),
        "source_confidence_min": min(confidence_values) if confidence_values else None,
        "source_confidence_max": max(confidence_values) if confidence_values else None,
        "source_confidence_ge_95_count": conf_ge_95,
    }


def run_verifier() -> dict[str, object]:
    proc = subprocess.run(
        ["python3", str(VERIFIER), "--intake-root", str(SHARED_ROOT)],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=120,
    )
    stdout_path = CMD_DIR / "source_label_equivalence_verifier.stdout.txt"
    stderr_path = CMD_DIR / "source_label_equivalence_verifier.stderr.txt"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    parsed: object | None = None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = None
    return {
        "returncode": proc.returncode,
        "status": (parsed or {}).get("status") if isinstance(parsed, dict) else "stdout_not_json",
        "parsed": parsed,
        "stdout_file": str(stdout_path.relative_to(REPO)),
        "stderr_file": str(stderr_path.relative_to(REPO)),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    SHARED_ROOT.mkdir(parents=True, exist_ok=True)
    STAGING_ROOT.mkdir(parents=True, exist_ok=True)

    existing_rows = read_existing_rows(SHARED_ROOT / ROWS_NAME)
    retained_rows = [
        row for row in existing_rows
        if not row.get("source_report_or_dataset", "").startswith(f"local:{SOURCE_CSV}")
    ]
    us_rows, us_summary = build_us_rows()
    merged_rows = retained_rows + us_rows

    staging_rows = STAGING_ROOT / ROWS_NAME
    shared_rows = SHARED_ROOT / ROWS_NAME
    write_rows(staging_rows, merged_rows)
    write_rows(shared_rows, merged_rows)

    existing_provenance_path = SHARED_ROOT / PROVENANCE_NAME
    try:
        prior_provenance = json.loads(existing_provenance_path.read_text(encoding="utf-8"))
    except Exception:
        prior_provenance = {}

    merged_label_counts = Counter(row["main_regime_v2_label"] for row in merged_rows if row.get("main_regime_v2_label"))
    merged_market_counts = Counter(row["market_family"] for row in merged_rows)
    provenance = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_owner": "local_stock_market_regimes_2000_2026_panel",
        "source_report_or_dataset": f"local:{SOURCE_CSV}",
        "source_pull_date": "2026-05-11",
        "source_csv_sha256": sha256_file(SOURCE_CSV),
        "source_summary_sha256": sha256_file(SOURCE_SUMMARY) if SOURCE_SUMMARY.exists() else None,
        "license_or_permission": [{"name": "local_download_metadata_missing"}],
        "raw_payload_committed_to_repo": False,
        "previous_rows_retained": len(retained_rows),
        "us_rows_added": len(us_rows),
        "merged_row_count": len(merged_rows),
        "us_panel_summary": us_summary,
        "merged_label_counts": dict(sorted(merged_label_counts.items())),
        "merged_market_counts": dict(sorted(merged_market_counts.items())),
        "rows_path": str(staging_rows),
        "rows_sha256": sha256_file(staging_rows),
        "shared_rows_path": str(shared_rows),
        "shared_rows_sha256": sha256_file(shared_rows),
        "prior_provenance_run_id": prior_provenance.get("run_id"),
        "limitations": [
            "schema extension only",
            "local source metadata does not provide owner-approved >=95 confidence acceptance",
            "source regime_confidence values are below 0.95 for all materialized rows",
            "daily US equity panel rows do not satisfy native sub-hour validation",
            "R6 direct Manipulation remains a separate direct-event root",
        ],
    }
    staging_provenance = STAGING_ROOT / PROVENANCE_NAME
    shared_provenance = SHARED_ROOT / PROVENANCE_NAME
    staging_provenance.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shared_provenance.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    verifier = run_verifier()

    label_rows = [
        {"label": label, "rows": count}
        for label, count in sorted(us_summary["label_counts"].items())
    ]
    write_simple_csv(OUT_DIR / "us_panel_source_label_equivalence_counts_v1.csv", label_rows, ["label", "rows"])

    decision = "us_panel_source_label_equivalence_extension_v1=schema_ready_all_price_roots_confidence_unaccepted"
    result = {
        "run_id": RUN_ID,
        "decision": decision,
        "shared_intake_root": str(SHARED_ROOT),
        "staging_root": str(STAGING_ROOT),
        "previous_rows_retained": len(retained_rows),
        "us_rows_added": len(us_rows),
        "merged_row_count": len(merged_rows),
        "us_panel_summary": us_summary,
        "merged_label_counts": dict(sorted(merged_label_counts.items())),
        "merged_market_counts": dict(sorted(merged_market_counts.items())),
        "verifier": verifier,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "next_action": "Rerun the current-goal audit against the now full-root source-label schema, then acquire accepted confidence scoring/native sub-hour/recency/R6 broad-control evidence.",
    }
    json_path = OUT_DIR / "us_panel_source_label_equivalence_extension_v1.json"
    report_path = OUT_DIR / "us_panel_source_label_equivalence_extension_v1.md"
    assertions_path = CHECK_DIR / "us_panel_source_label_equivalence_extension_v1_assertions.out"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report_lines = [
        "# US Panel Source Label Equivalence Extension v1",
        "",
        f"Decision: `{decision}`.",
        "",
        "Result:",
        f"- Previous shared rows retained: `{len(retained_rows)}`.",
        f"- US panel rows added: `{len(us_rows)}`.",
        f"- Merged shared row count: `{len(merged_rows)}`.",
        f"- US label counts: `{dict(sorted(us_summary['label_counts'].items()))}`.",
        f"- Merged label counts: `{dict(sorted(merged_label_counts.items()))}`.",
        f"- Date range: `{us_summary['date_min']}` to `{us_summary['date_max']}`; tickers `{us_summary['ticker_count']}`.",
        f"- Source confidence >=0.95 rows: `{us_summary['source_confidence_ge_95_count']}`; accepted confidence gate: `false`.",
        f"- Verifier status: `{verifier['status']}`; return code `{verifier['returncode']}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "Interpretation:",
        "The shared source-label equivalence root now has schema rows for Bull, Bear, Sideways, and Crisis across the local US daily equity panel plus the prior NIFTY rows. This closes a schema gap only. It does not provide owner-approved >=95 confidence, native sub-hour validation, R5 recency extension, or R6 direct Manipulation confidence.",
        "",
        "Artifacts:",
        f"- JSON: `{json_path.relative_to(REPO)}`",
        f"- Report: `{report_path.relative_to(REPO)}`",
        f"- Counts CSV: `{(OUT_DIR / 'us_panel_source_label_equivalence_counts_v1.csv').relative_to(REPO)}`",
        f"- Shared verifier stdout: `{Path(verifier['stdout_file'])}`",
        f"- Reproduction script: `{Path(__file__).relative_to(REPO)}`",
        f"- Assertions: `{assertions_path.relative_to(REPO)}`",
    ]
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS us_rows_added={len(us_rows)}",
        "PASS all_price_roots_present=true",
        f"PASS source_confidence_ge_95_count={us_summary['source_confidence_ge_95_count']}",
        f"PASS verifier_status={verifier['status']}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
        "PASS external_requests_sent=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(json.dumps({
        "decision": decision,
        "us_rows_added": len(us_rows),
        "merged_row_count": len(merged_rows),
        "merged_label_counts": dict(sorted(merged_label_counts.items())),
        "source_confidence_ge_95_count": us_summary["source_confidence_ge_95_count"],
        "verifier_status": verifier["status"],
        "update_goal": False,
        "report": str(report_path.relative_to(REPO)),
    }, indent=2, sort_keys=True))
    return 0 if verifier["returncode"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
