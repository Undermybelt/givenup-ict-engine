#!/usr/bin/env python3
"""Build a fail-closed intake manifest for source-panel recency extension."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T165405+0800-codex-source-panel-recency-extension-manifest-v1"
RUN_ROOT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1"
)
OUT_DIR = RUN_ROOT / "source-panel-recency"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
SOURCE_PANEL = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
INVENTORY = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T162942-codex-daily-main-root-source-inventory-v1/"
    "daily-main-root-inventory/daily_main_root_source_inventory_v1.json"
)

OUT_JSON = OUT_DIR / "source_panel_recency_extension_manifest_v1.json"
OUT_MD = OUT_DIR / "source_panel_recency_extension_manifest_v1.md"
OUT_CSV = OUT_DIR / "source_panel_recency_extension_required_files_v1.csv"
OUT_VERIFIER = OUT_DIR / "source_panel_recency_extension_verifier_v1.py"
OUT_ASSERT = CHECK_DIR / "source_panel_recency_extension_manifest_v1_assertions.out"

ROOTS = {"Bull", "Bear", "Sideways", "Crisis"}
AUDIT_DATE = date(2026, 5, 11)


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_inventory() -> dict[str, Any]:
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


def source_panel_summary() -> dict[str, Any]:
    tickers: set[str] = set()
    columns: list[str] = []
    row_count = 0
    min_date: date | None = None
    max_date: date | None = None
    root_counts = {root: 0 for root in sorted(ROOTS)}
    residual_count = 0
    with SOURCE_PANEL.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        for row in reader:
            row_count += 1
            tickers.add(row["ticker"])
            day = datetime.strptime(row["date"], "%Y-%m-%d").date()
            min_date = day if min_date is None else min(min_date, day)
            max_date = day if max_date is None else max(max_date, day)
            label = row["regime_label"]
            if label in root_counts:
                root_counts[label] += 1
            else:
                residual_count += 1
    return {
        "columns": columns,
        "row_count": row_count,
        "ticker_count": len(tickers),
        "tickers": sorted(tickers),
        "date_min": str(min_date),
        "date_max": str(max_date),
        "root_counts": root_counts,
        "residual_count": residual_count,
    }


def weekdays_after(start_exclusive: date, end_inclusive: date) -> list[date]:
    days: list[date] = []
    cur = start_exclusive + timedelta(days=1)
    while cur <= end_inclusive:
        if cur.weekday() < 5:
            days.append(cur)
        cur += timedelta(days=1)
    return days


def verifier_source(columns: list[str], tickers: list[str], last_date: str) -> str:
    return f'''#!/usr/bin/env python3
"""Fail-closed verifier for source-panel recency extension rows."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path


REQUIRED_COLUMNS = {repr(columns)}
EXPECTED_TICKERS = set({repr(tickers)})
ROOTS = {repr(sorted(ROOTS))}
LAST_SOURCE_DATE = datetime.strptime({last_date!r}, "%Y-%m-%d").date()
REQUIRED_FILES = {{
    "extension_rows": "stock_market_regimes_2026_extension.csv",
    "provenance_manifest": "source_panel_recency_provenance.json",
}}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intake-root", required=True)
    args = parser.parse_args()
    root = Path(args.intake_root)
    rows_path = root / REQUIRED_FILES["extension_rows"]
    provenance_path = root / REQUIRED_FILES["provenance_manifest"]
    missing = [str(path) for path in [rows_path, provenance_path] if not path.exists()]
    if missing:
        print(json.dumps({{"status": "blocked", "reason": "missing_required_files", "missing_files": missing}}, indent=2))
        return 2

    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    with rows_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in (reader.fieldnames or [])]
        if missing_cols:
            print(json.dumps({{"status": "blocked", "reason": "missing_columns", "missing_columns": missing_cols}}, indent=2))
            return 2
        rows = list(reader)
    if not rows:
        print(json.dumps({{"status": "blocked", "reason": "empty_extension_rows"}}, indent=2))
        return 2
    bad_dates = []
    bad_labels = []
    seen = set()
    duplicates = 0
    tickers = set()
    for row in rows:
        key = (row["date"], row["ticker"])
        if key in seen:
            duplicates += 1
        seen.add(key)
        tickers.add(row["ticker"])
        day = datetime.strptime(row["date"], "%Y-%m-%d").date()
        if day <= LAST_SOURCE_DATE:
            bad_dates.append(row["date"])
        if row["regime_label"] not in ROOTS:
            bad_labels.append(row["regime_label"])
    unknown_tickers = sorted(tickers - EXPECTED_TICKERS)
    if bad_dates or bad_labels or duplicates or unknown_tickers:
        print(json.dumps({{
            "status": "blocked",
            "reason": "extension_rows_failed_guardrails",
            "bad_dates_sample": bad_dates[:10],
            "bad_labels_sample": sorted(set(bad_labels))[:10],
            "duplicates": duplicates,
            "unknown_tickers": unknown_tickers[:20],
        }}, indent=2))
        return 2
    print(json.dumps({{
        "status": "schema_ready_unscored",
        "extension_rows": len(rows),
        "ticker_count": len(tickers),
        "date_min": min(row["date"] for row in rows),
        "date_max": max(row["date"] for row in rows),
        "provenance_keys": sorted(provenance.keys()),
        "next": "append to source panel in /tmp and rerun daily/weekly/monthly/1h source gates"
    }}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    inventory = load_inventory()
    summary = source_panel_summary()
    last_date = datetime.strptime(summary["date_max"], "%Y-%m-%d").date()
    missing_weekdays = weekdays_after(last_date, AUDIT_DATE)
    estimated_rows = len(missing_weekdays) * summary["ticker_count"]
    required_files = [
        {
            "file": "stock_market_regimes_2026_extension.csv",
            "destination": "/tmp/ict-engine-source-panel-recency-extension/stock_market_regimes_2026_extension.csv",
            "purpose": "source-owned MainRegimeV2 rows after 2026-01-30 using the existing source-panel columns",
            "required": True,
        },
        {
            "file": "source_panel_recency_provenance.json",
            "destination": "/tmp/ict-engine-source-panel-recency-extension/source_panel_recency_provenance.json",
            "purpose": "source identity, owner, pull date, generation/export notes, and non-proxy attestation",
            "required": True,
        },
    ]
    manifest = {
        "run_id": RUN_ID,
        "artifact_type": "source_panel_recency_extension_manifest_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": repo_rel(BOARD),
        "board_sha256_at_run": sha256(BOARD),
        "purpose": "Make the post-2026-01-30 source-label recency gap executable without generating proxy labels.",
        "source_panel": {
            **summary,
            "sha256": sha256(SOURCE_PANEL),
            "inventory_gate": inventory["decision"]["gate_result"],
        },
        "recency_gap": {
            "last_source_date": summary["date_max"],
            "audit_date": str(AUDIT_DATE),
            "weekday_sessions_after_last_source_date": len(missing_weekdays),
            "estimated_extension_rows_for_existing_ticker_universe": estimated_rows,
            "first_missing_weekday": str(missing_weekdays[0]) if missing_weekdays else "",
            "last_missing_weekday": str(missing_weekdays[-1]) if missing_weekdays else "",
        },
        "required_files": required_files,
        "verifier": {
            "path": repo_rel(OUT_VERIFIER),
            "status": "ready_fail_closed",
            "command": (
                "python3 "
                + repo_rel(OUT_VERIFIER)
                + " --intake-root /tmp/ict-engine-source-panel-recency-extension"
            ),
            "pass_means": "extension rows match schema/date/ticker/root guardrails; calibration gates still rerun next",
        },
        "guardrails": [
            "Do not generate labels from fresh OHLCV/provider bars.",
            "Do not use HMM/model/future-return labels as source labels.",
            "Do not fill NQ/QQQ/futures/crypto/FX equivalence from this U.S. stock/index extension.",
            "Do not mutate the original source-panel file; combine in /tmp for reruns.",
        ],
        "decision": {
            "gate_result": "source_panel_recency_extension_manifest_v1_ready_rows_not_acquired",
            "extension_rows_added": 0,
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": (
            "Place source-owned recency extension rows and provenance under "
            "/tmp/ict-engine-source-panel-recency-extension, run the fail-closed verifier, "
            "then rerun daily/weekly/monthly/1h source gates against a /tmp combined panel."
        ),
    }
    OUT_VERIFIER.write_text(verifier_source(summary["columns"], summary["tickers"], summary["date_max"]), encoding="utf-8")
    write_csv(OUT_CSV, required_files, ["file", "destination", "purpose", "required"])
    OUT_JSON.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Source Panel Recency Extension Manifest v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This turns the post-`2026-01-30` source-label recency gap into an executable intake package. It does not generate labels.",
        "",
        "## Result",
        "",
        f"- Current source panel max date: `{summary['date_max']}`.",
        f"- Audit date: `{AUDIT_DATE}`.",
        f"- Weekday sessions after max date: `{len(missing_weekdays)}`.",
        f"- Estimated extension rows for the existing `39` tickers: `{estimated_rows}`.",
        "- Extension rows added: `0`.",
        "- Gate result: `source_panel_recency_extension_manifest_v1=ready_rows_not_acquired`.",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Required Files",
        "",
        "| File | Destination | Purpose |",
        "|---|---|---|",
    ]
    for row in required_files:
        lines.append(f"| `{row['file']}` | `{row['destination']}` | {row['purpose']} |")
    lines.extend(
        [
            "",
            "## Verifier",
            "",
            "```bash",
            manifest["verifier"]["command"],
            "```",
            "",
            "The verifier is fail-closed for missing files, schema drift, non-recency dates, unknown tickers, duplicate date/ticker rows, and non-root labels.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    failures = []
    if summary["date_max"] != "2026-01-30":
        failures.append("unexpected_source_panel_max_date")
    if estimated_rows <= 0:
        failures.append("no_recency_gap_detected")
    if manifest["decision"]["full_objective_achieved"]:
        failures.append("must_not_mark_full_objective_complete")
    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={manifest['board_sha256_at_run']}",
        f"source_panel_date_max={summary['date_max']}",
        f"weekday_sessions_after_last_source_date={len(missing_weekdays)}",
        f"estimated_extension_rows={estimated_rows}",
        "extension_rows_added=0",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "full_objective_achieved=false",
        "update_goal=false",
        f"assertion_status={'FAIL' if failures else 'PASS'}",
    ]
    if failures:
        assertions.append("failures=" + ",".join(failures))
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
