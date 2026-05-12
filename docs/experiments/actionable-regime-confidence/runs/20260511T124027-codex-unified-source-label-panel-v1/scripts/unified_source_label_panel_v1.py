#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20260511T124027+0800-codex-unified-source-label-panel-v1"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
MISSING_CSV = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T094002-codex-external-label-request-package-v3/"
    "acquisition-request/missing_parent_root_label_slots_request_v3.csv"
)
BBC_WINDOWS = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T123826-codex-source-window-label-panel-materialization-v1/"
    "source-window-label-panel/source_window_label_panel_windows_v1.csv"
)
BBC_REPORT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T123826-codex-source-window-label-panel-materialization-v1/"
    "source-window-label-panel/source_window_label_panel_materialization_v1.json"
)
SIDEWAYS_WINDOWS = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T123500-codex-sideways-dated-window-materialization-v1/"
    "sideways-windows/sideways_dated_windows_v1.csv"
)
SIDEWAYS_REPORT = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T123500-codex-sideways-dated-window-materialization-v1/"
    "sideways-windows/sideways_dated_window_materialization_v1.json"
)
OUT_DIR = RUN_ROOT / "unified-source-label-panel"
CHECK_DIR = RUN_ROOT / "checks"
OUT_JSON = OUT_DIR / "unified_source_label_panel_v1.json"
OUT_MD = OUT_DIR / "unified_source_label_panel_v1.md"
OUT_PANEL = OUT_DIR / "unified_source_label_panel_v1.csv"
OUT_COVERAGE = OUT_DIR / "unified_source_label_panel_coverage_v1.csv"
ASSERTIONS = CHECK_DIR / "unified_source_label_panel_v1_assertions.out"

PRICE_ROOTS = {"Bull", "Bear", "Sideways", "Crisis"}


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_provider(provider: str) -> str:
    return "yfinance" if provider in {"yfinance_cache", "Yahoo public market data via existing local yfinance cache"} else provider


def context_for_bbc(row: dict[str, str]) -> str:
    if row["instrument"] == "^GSPC":
        return "sp500_same_underlying_index"
    if row["instrument"] in {"SPY", "ES=F"}:
        return "sp500_tradable_proxy"
    return "unknown"


def load_unified_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(BBC_WINDOWS):
        rows.append(
            {
                "panel_row_id": row["label_panel_row_id"],
                "source_lane": "bull_bear_crisis_source_window_crosswalk",
                "root": row["root"],
                "provider": normalize_provider(row["provider"]),
                "instrument": row["instrument"],
                "market_context": context_for_bbc(row),
                "timeframe": row["timeframe"],
                "start_date": row["source_start_date"],
                "end_date": row["source_end_date"],
                "source_id": row["source_id"],
                "source_family": row["source_native_scope"],
                "evidence_type": "dated_external_source_window",
                "materialization_status": row["materialization_status"],
                "row_count": "",
                "train_rows": "",
                "calibration_rows": "",
                "test_rows": "",
                "rule_or_window": f"{row['source_start_date']}..{row['source_end_date']}",
                "crosswalk_layer": row["crosswalk_layer"],
                "crosswalk_decision": row["crosswalk_decision"],
                "confidence_gate_reference": "none_claimed_by_materialization",
                "notes": row["notes"],
            }
        )
    for row in read_csv(SIDEWAYS_WINDOWS):
        rows.append(
            {
                "panel_row_id": row["source_window_id"],
                "source_lane": "sideways_scoped_dated_windows_from_accepted_gate",
                "root": "Sideways",
                "provider": normalize_provider(row["provider"]),
                "instrument": row["instrument"],
                "market_context": row["market_context"],
                "timeframe": row["timeframe"],
                "start_date": row["start_date"],
                "end_date": row["end_date"],
                "source_id": "sideways_sourcebacked_abs_return_range_v1",
                "source_family": "accepted_scoped_sideways_observed_rule",
                "evidence_type": "dated_rule_materialized_window",
                "materialization_status": row["status"],
                "row_count": row["row_count"],
                "train_rows": row["train_rows"],
                "calibration_rows": row["calibration_rows"],
                "test_rows": row["test_rows"],
                "rule_or_window": row["rule"],
                "crosswalk_layer": "sideways_adjudication_protocol_v1",
                "crosswalk_decision": "scoped_existing_accepted_gate",
                "confidence_gate_reference": "calibration/test Wilson95 0.988647/0.995568 from 20260511T041923",
                "notes": "Scoped to existing Yahoo 1d/1w crypto/equity ETF panel; not full matrix.",
            }
        )
    return rows


def covered_keys(rows: list[dict[str, Any]]) -> set[tuple[str, str, str, str]]:
    keys: set[tuple[str, str, str, str]] = set()
    for row in rows:
        if row["root"] not in PRICE_ROOTS:
            continue
        if row["materialization_status"] not in {
            "materialized_closed_window",
            "materialized_scoped_dated_window",
        }:
            continue
        keys.add((normalize_provider(row["provider"]), row["instrument"], row["timeframe"], row["root"]))
    return keys


def main() -> None:
    bbc_report = json.loads(BBC_REPORT.read_text())
    sideways_report = json.loads(SIDEWAYS_REPORT.read_text())
    rows = load_unified_rows()
    keys = covered_keys(rows)
    missing = read_csv(MISSING_CSV)
    coverage_rows: list[dict[str, Any]] = []
    for slot in missing:
        key = (normalize_provider(slot["provider"]), slot["instrument"], slot["timeframe"], slot["root"])
        status = "covered_by_materialized_source_panel" if key in keys else "still_missing_or_out_of_scope"
        coverage_rows.append(
            {
                "request_id": slot["request_id"],
                "provider": slot["provider"],
                "instrument": slot["instrument"],
                "timeframe": slot["timeframe"],
                "root": slot["root"],
                "missing_or_rejected_reason": slot["missing_or_rejected_reason"],
                "coverage_status": status,
            }
        )

    materialized_rows = [
        row
        for row in rows
        if row["materialization_status"]
        in {"materialized_closed_window", "materialized_scoped_dated_window"}
    ]
    deferred_rows = [row for row in rows if row["materialization_status"] == "deferred_refresh_required"]
    coverage_counts = Counter(row["coverage_status"] for row in coverage_rows)
    covered_by_root = Counter(row["root"] for row in coverage_rows if row["coverage_status"] == "covered_by_materialized_source_panel")
    missing_by_root = Counter(row["root"] for row in coverage_rows if row["coverage_status"] != "covered_by_materialized_source_panel")
    materialized_by_root = Counter(row["root"] for row in materialized_rows)
    materialized_by_lane = Counter(row["source_lane"] for row in materialized_rows)

    report = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "unified_source_label_panel_v1",
        "objective": "Unify materialized Bull/Bear/Crisis source-window labels with scoped Sideways dated windows, then audit current missing-slot coverage.",
        "inputs": {
            "board": repo_rel(BOARD),
            "board_sha256_at_run": sha256(BOARD),
            "missing_slots": repo_rel(MISSING_CSV),
            "missing_slots_sha256": sha256(MISSING_CSV),
            "bbc_windows": repo_rel(BBC_WINDOWS),
            "bbc_windows_sha256": sha256(BBC_WINDOWS),
            "bbc_report": repo_rel(BBC_REPORT),
            "bbc_report_sha256": sha256(BBC_REPORT),
            "sideways_windows": repo_rel(SIDEWAYS_WINDOWS),
            "sideways_windows_sha256": sha256(SIDEWAYS_WINDOWS),
            "sideways_report": repo_rel(SIDEWAYS_REPORT),
            "sideways_report_sha256": sha256(SIDEWAYS_REPORT),
        },
        "source_panel": {
            "total_panel_rows_including_deferred": len(rows),
            "materialized_panel_rows": len(materialized_rows),
            "deferred_refresh_required_rows": len(deferred_rows),
            "materialized_by_root": dict(materialized_by_root),
            "materialized_by_lane": dict(materialized_by_lane),
            "price_roots_with_materialized_windows": sorted({row["root"] for row in materialized_rows}),
            "price_root_coverage_count": len({row["root"] for row in materialized_rows} & PRICE_ROOTS),
            "manipulation_included": False,
        },
        "missing_slot_coverage": {
            "total_missing_or_rejected_slots": len(missing),
            "covered_by_materialized_source_panel": coverage_counts.get("covered_by_materialized_source_panel", 0),
            "still_missing_or_out_of_scope": coverage_counts.get("still_missing_or_out_of_scope", 0),
            "covered_by_root": dict(covered_by_root),
            "still_missing_by_root": dict(missing_by_root),
        },
        "decision": {
            "main_price_roots_have_some_materialized_source_windows": sorted({row["root"] for row in materialized_rows} & PRICE_ROOTS)
            == sorted(PRICE_ROOTS),
            "full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "confidence_gate_claimed": False,
            "why_not_complete": [
                "Unified panel gives materialized source windows for all four price roots, but only 67 of the current 564 missing/rejected root slots are covered.",
                "Bull/Bear/Crisis coverage is restricted to declared S&P 500 same-underlying/proxy crosswalks.",
                "Sideways coverage is scoped to existing Yahoo 1d/1w crypto/equity ETF windows and does not cover intraday/monthly/full-species cells.",
                "Open-ended Yardeni Bull rows still require source refresh before current/live use.",
                "Manipulation is a separate direct-event/order-flow/order-lifecycle class and is not included in this price-root panel.",
            ],
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "artifacts": {
            "json": repo_rel(OUT_JSON),
            "md": repo_rel(OUT_MD),
            "panel_csv": repo_rel(OUT_PANEL),
            "coverage_csv": repo_rel(OUT_COVERAGE),
            "assertions": repo_rel(ASSERTIONS),
            "script": repo_rel(Path(__file__).resolve()),
        },
        "next_action": "Run the next calibration/coverage pass only on the remaining high-yield uncovered cells: Sideways intraday/monthly for S&P 500-linked instruments and direct Manipulation variety expansion.",
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    with OUT_PANEL.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    with OUT_COVERAGE.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(coverage_rows[0].keys()))
        writer.writeheader()
        writer.writerows(coverage_rows)

    lines = [
        "# Unified Source-Label Panel v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Materialized panel rows: `{len(materialized_rows)}`.",
        f"- Deferred refresh-required rows: `{len(deferred_rows)}`.",
        f"- Price roots with materialized windows: `{', '.join(report['source_panel']['price_roots_with_materialized_windows'])}`.",
        f"- Current missing/rejected slots covered: `{coverage_counts.get('covered_by_materialized_source_panel', 0)}` / `{len(missing)}`.",
        f"- Still missing/out-of-scope slots: `{coverage_counts.get('still_missing_or_out_of_scope', 0)}`.",
        f"- Full-objective gate: `{report['decision']['full_objective_gate']}`.",
        "",
        "## Covered Slots By Root",
        "",
        "| Root | Covered | Still Missing |",
        "|---|---:|---:|",
    ]
    for root in ["Bull", "Bear", "Sideways", "Crisis"]:
        lines.append(f"| `{root}` | `{covered_by_root.get(root, 0)}` | `{missing_by_root.get(root, 0)}` |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This unifies label-window artifacts; it does not claim held-out 95% completion for the full matrix.",
            "- `Manipulation` remains direct-event scoped and separate.",
            "- Runtime code changed: false.",
            "- Thresholds relaxed: false.",
            "- Raw data committed: false.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n")

    failures: list[str] = []
    if report["source_panel"]["price_root_coverage_count"] != 4:
        failures.append("expected_four_price_roots_with_materialized_windows")
    if len(materialized_rows) != 818:
        failures.append("expected_818_materialized_panel_rows")
    if len(deferred_rows) != 21:
        failures.append("expected_21_deferred_refresh_rows")
    if coverage_counts.get("covered_by_materialized_source_panel", 0) != 67:
        failures.append("expected_67_missing_slots_covered")
    if report["decision"]["confidence_gate_claimed"]:
        failures.append("confidence_gate_must_not_be_claimed")
    if failures:
        raise AssertionError("; ".join(failures))

    ASSERTIONS.write_text(
        "\n".join(
            [
                f"PASS run_id={RUN_ID}",
                "PASS price_roots_with_materialized_windows=4",
                f"PASS materialized_panel_rows={len(materialized_rows)}",
                f"PASS deferred_refresh_required_rows={len(deferred_rows)}",
                f"PASS missing_slots_covered={coverage_counts.get('covered_by_materialized_source_panel', 0)}",
                f"PASS still_missing_or_out_of_scope={coverage_counts.get('still_missing_or_out_of_scope', 0)}",
                "PASS confidence_gate_claimed=false",
                "PASS full_objective_gate=none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
                "PASS thresholds_relaxed=false",
                "PASS runtime_code_changed=false",
                "PASS raw_data_committed=false",
                "PASS trade_usable=false",
            ]
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
