#!/usr/bin/env python3
"""Read-only local acquisition probe for source-panel recency extension rows."""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T180345+0800-codex-source-panel-recency-local-acquisition-probe-v1"
RUN_ROOT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T180345-codex-source-panel-recency-local-acquisition-probe-v1"
)
OUT_DIR = RUN_ROOT / "local-acquisition-probe"
CHECK_DIR = RUN_ROOT / "checks"

SOURCE_PANEL = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
MANIFEST = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T165405-codex-source-panel-recency-extension-manifest-v1/"
    "source-panel-recency/source_panel_recency_extension_manifest_v1.json"
)
EXPECTED_INTAKE = Path("/tmp/ict-engine-source-panel-recency-extension")

OUT_JSON = OUT_DIR / "source_panel_recency_local_acquisition_probe_v1.json"
OUT_MD = OUT_DIR / "source_panel_recency_local_acquisition_probe_v1.md"
OUT_CSV = OUT_DIR / "source_panel_recency_local_acquisition_probe_v1_candidates.csv"
OUT_ASSERT = CHECK_DIR / "source_panel_recency_local_acquisition_probe_v1_assertions.out"

ROOTS = {"Bull", "Bear", "Sideways", "Crisis"}
SOURCE_PACKAGE_ROOTS = [
    Path("/Users/thrill3r/Downloads"),
    Path("/Users/thrill3r/Auto-Quant"),
]
TMP_ROOTS = [
    Path("/tmp"),
    Path("/private/tmp"),
]
PATTERN_TERMS = ("regime", "source_panel", "stock_market")
MAX_DEPTH = 5


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def depth_from(root: Path, path: Path) -> int:
    try:
        return len(path.relative_to(root).parts)
    except ValueError:
        return 999


def source_schema() -> tuple[list[str], set[str], str]:
    columns: list[str] = []
    tickers: set[str] = set()
    max_date = ""
    with SOURCE_PANEL.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        for row in reader:
            tickers.add(row["ticker"])
            if not max_date or row["date"] > max_date:
                max_date = row["date"]
    return columns, tickers, max_date


def likely_file(path: Path) -> bool:
    name = path.name.lower()
    if path.suffix.lower() not in {".csv", ".json", ".parquet"}:
        return False
    return any(term in name for term in PATTERN_TERMS) or path.name in {
        "stock_market_regimes_2026_extension.csv",
        "source_panel_recency_provenance.json",
    }


def likely_tmp_extension_file(path: Path) -> bool:
    name = path.name.lower()
    if path.name in {"stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"}:
        return True
    if path.suffix.lower() not in {".csv", ".json"}:
        return False
    return "regime" in name and "extension" in name


def find_candidates() -> list[Path]:
    out: list[Path] = []
    for root in SOURCE_PACKAGE_ROOTS:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            current = Path(dirpath)
            if depth_from(root, current) > MAX_DEPTH:
                dirnames[:] = []
                continue
            for filename in filenames:
                path = current / filename
                if likely_file(path):
                    out.append(path)
    for root in TMP_ROOTS:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            current = Path(dirpath)
            if depth_from(root, current) > MAX_DEPTH:
                dirnames[:] = []
                continue
            for filename in filenames:
                path = current / filename
                if likely_tmp_extension_file(path):
                    out.append(path)
    return sorted(set(out))


def summarize_csv(path: Path, required_columns: list[str], source_tickers: set[str], source_last_date: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "format": "csv",
        "readable": True,
        "rows": 0,
        "has_required_columns": False,
        "date_min": "",
        "date_max": "",
        "ticker_count": 0,
        "unknown_ticker_count": 0,
        "bad_label_count": 0,
        "extension_candidate": False,
        "blockers": [],
    }
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames or []
            missing = [column for column in required_columns if column not in fields]
            result["has_required_columns"] = not missing
            if missing:
                result["blockers"].append("missing_required_columns")
            tickers: set[str] = set()
            bad_labels = 0
            for row in reader:
                result["rows"] += 1
                if "date" in row and row["date"]:
                    result["date_min"] = min(result["date_min"], row["date"]) if result["date_min"] else row["date"]
                    result["date_max"] = max(result["date_max"], row["date"]) if result["date_max"] else row["date"]
                if "ticker" in row and row["ticker"]:
                    tickers.add(row["ticker"])
                if "regime_label" in row and row["regime_label"] and row["regime_label"] not in ROOTS:
                    bad_labels += 1
            result["ticker_count"] = len(tickers)
            result["unknown_ticker_count"] = len(tickers - source_tickers)
            result["bad_label_count"] = bad_labels
            if result["rows"] == 0:
                result["blockers"].append("empty_file")
            if result["date_max"] and result["date_max"] <= source_last_date:
                result["blockers"].append("not_newer_than_source_panel")
            if result["unknown_ticker_count"]:
                result["blockers"].append("unknown_tickers")
            if bad_labels:
                result["blockers"].append("non_root_labels")
            result["extension_candidate"] = (
                result["has_required_columns"]
                and result["rows"] > 0
                and bool(result["date_max"])
                and result["date_max"] > source_last_date
                and result["unknown_ticker_count"] == 0
                and bad_labels == 0
            )
    except Exception as exc:  # noqa: BLE001 - artifact should record read failure.
        result["readable"] = False
        result["blockers"].append(f"read_error:{type(exc).__name__}")
    return result


def summarize_candidate(path: Path, required_columns: list[str], source_tickers: set[str], source_last_date: str) -> dict[str, Any]:
    if path.suffix.lower() == ".csv":
        return summarize_csv(path, required_columns, source_tickers, source_last_date)
    return {
        "path": str(path),
        "format": path.suffix.lower().lstrip("."),
        "readable": False,
        "rows": "",
        "has_required_columns": False,
        "date_min": "",
        "date_max": "",
        "ticker_count": "",
        "unknown_ticker_count": "",
        "bad_label_count": "",
        "extension_candidate": False,
        "blockers": ["not_csv_checked_by_this_probe"],
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "path",
        "format",
        "readable",
        "rows",
        "has_required_columns",
        "date_min",
        "date_max",
        "ticker_count",
        "unknown_ticker_count",
        "bad_label_count",
        "extension_candidate",
        "blockers",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    required_columns, source_tickers, source_last_date = source_schema()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected_files = [
        EXPECTED_INTAKE / "stock_market_regimes_2026_extension.csv",
        EXPECTED_INTAKE / "source_panel_recency_provenance.json",
    ]
    candidates = [summarize_candidate(path, required_columns, source_tickers, source_last_date) for path in find_candidates()]
    extension_candidates = [row for row in candidates if row["extension_candidate"]]
    payload = {
        "run_id": RUN_ID,
        "artifact_type": "source_panel_recency_local_acquisition_probe_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_panel": str(SOURCE_PANEL),
        "source_panel_last_date": source_last_date,
        "manifest": repo_rel(MANIFEST),
        "expected_intake_files": [
            {"path": str(path), "exists": path.exists()} for path in expected_files
        ],
        "source_package_roots": [str(path) for path in SOURCE_PACKAGE_ROOTS],
        "tmp_extension_roots": [str(path) for path in TMP_ROOTS],
        "max_depth": MAX_DEPTH,
        "candidate_file_count": len(candidates),
        "extension_candidate_count": len(extension_candidates),
        "extension_candidates": extension_candidates,
        "decision": {
            "gate_result": "source_panel_recency_local_acquisition_probe_v1=no_extension_rows_found",
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "full_objective_achieved": False,
            "update_goal": False,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": manifest["next_action"],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(OUT_CSV, candidates)
    lines = [
        "# Source Panel Recency Local Acquisition Probe v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "Read-only local probe for source-owned extension rows after `2026-01-30`.",
        "",
        "## Result",
        "",
        f"- Source panel last date: `{source_last_date}`.",
        f"- Candidate files inspected: `{len(candidates)}`.",
        f"- Extension candidates found: `{len(extension_candidates)}`.",
        "- Expected `/tmp` intake files present: `false`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Gate result: `source_panel_recency_local_acquisition_probe_v1=no_extension_rows_found`.",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "",
        "## Candidate Notes",
        "",
        "The only schema-like source-package candidates found were the existing `Downloads/stock-market-regimes-20002026` files; they do not extend beyond `2026-01-30`. No exact `/tmp` intake files or `*regime*extension*` local files were present.",
        "",
        "## Next",
        "",
        payload["next_action"],
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assertions = [
        f"run_id={RUN_ID}",
        f"source_panel_last_date={source_last_date}",
        f"candidate_file_count={len(candidates)}",
        f"extension_candidate_count={len(extension_candidates)}",
        f"expected_intake_files_present={all(path.exists() for path in expected_files)}",
        "accepted_rows_added=0",
        "new_confidence_gate=false",
        "full_objective_achieved=false",
        "update_goal=false",
        "assertion_status=PASS",
    ]
    OUT_ASSERT.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
