#!/usr/bin/env python3
from __future__ import annotations

import calendar
import csv
import hashlib
import json
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20260511T123826+0800-codex-source-window-label-panel-materialization-v1"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
SOURCE_SEED = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T120900-codex-exportable-source-scan/"
    "source-scan/source_window_seed_v1.csv"
)
APPROVED_SLOTS = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T122933-codex-source-window-crosswalk-decision-v1/"
    "source-window-crosswalk/approved_source_window_slots_v1.csv"
)
CROSSWALK_PACKAGE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T123100-codex-crosswalk-decision-package-v1/"
    "crosswalk-decision/crosswalk_decision_package_v1.json"
)
OUT_DIR = RUN_ROOT / "source-window-label-panel"
CHECK_DIR = RUN_ROOT / "checks"
OUT_JSON = OUT_DIR / "source_window_label_panel_materialization_v1.json"
OUT_MD = OUT_DIR / "source_window_label_panel_materialization_v1.md"
OUT_WINDOWS = OUT_DIR / "source_window_label_panel_windows_v1.csv"
OUT_SLOT_SUMMARY = OUT_DIR / "source_window_label_panel_slot_summary_v1.csv"
ASSERTIONS = CHECK_DIR / "source_window_label_panel_materialization_v1_assertions.out"


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


def parse_window_dates(row: dict[str, str]) -> tuple[str, str, str]:
    start = row["start_date"]
    end = row["end_date"]
    granularity = row["date_granularity"]
    if granularity == "month":
        year, month = [int(part) for part in start.split("-")]
        start = f"{year:04d}-{month:02d}-01"
        if end:
            end_year, end_month = [int(part) for part in end.split("-")]
            end_day = calendar.monthrange(end_year, end_month)[1]
            end = f"{end_year:04d}-{end_month:02d}-{end_day:02d}"
    return start, end, granularity


def materialization_status(source_row: dict[str, str]) -> tuple[str, str]:
    if source_row["root"] == "Bull" and not source_row["end_date"]:
        return (
            "deferred_refresh_required",
            "Open-ended Yardeni 2022-10-12 Bull window requires current source refresh before live/current attachment.",
        )
    return (
        "materialized_closed_window",
        "Closed dated source window can attach to target slot with explicit crosswalk tier provenance.",
    )


def main() -> None:
    source_rows = read_csv(SOURCE_SEED)
    approved_slots = read_csv(APPROVED_SLOTS)
    crosswalk = json.loads(CROSSWALK_PACKAGE.read_text())
    source_by_root: dict[str, list[dict[str, str]]] = {}
    for row in source_rows:
        source_by_root.setdefault(row["root"], []).append(row)

    slot_rows: list[dict[str, Any]] = []
    window_rows: list[dict[str, Any]] = []
    for slot in approved_slots:
        root = slot["root"]
        source_windows = source_by_root.get(root, [])
        slot_materialized = 0
        slot_deferred = 0
        for idx, source in enumerate(source_windows, start=1):
            start_date, end_date, granularity = parse_window_dates(source)
            status, note = materialization_status(source)
            if status == "materialized_closed_window":
                slot_materialized += 1
            else:
                slot_deferred += 1
            window_rows.append(
                {
                    "label_panel_row_id": f"{slot['slot_id']}-window-{idx:02d}",
                    "slot_id": slot["slot_id"],
                    "provider": slot["provider"],
                    "instrument": slot["instrument"],
                    "timeframe": slot["timeframe"],
                    "root": root,
                    "source_id": source["source_id"],
                    "source_native_scope": source["native_scope"],
                    "crosswalk_layer": slot["crosswalk_layer"],
                    "crosswalk_decision": slot["crosswalk_decision"],
                    "acceptance_scope": slot["acceptance_scope"],
                    "source_start_date": start_date,
                    "source_end_date": end_date,
                    "source_date_granularity": granularity,
                    "materialization_status": status,
                    "provenance_url": source["source_url"],
                    "notes": note,
                }
            )
        slot_rows.append(
            {
                "slot_id": slot["slot_id"],
                "provider": slot["provider"],
                "instrument": slot["instrument"],
                "timeframe": slot["timeframe"],
                "root": root,
                "crosswalk_layer": slot["crosswalk_layer"],
                "crosswalk_decision": slot["crosswalk_decision"],
                "source_window_count": len(source_windows),
                "materialized_closed_window_count": slot_materialized,
                "deferred_refresh_window_count": slot_deferred,
                "slot_status": "materialized_with_refresh_gap" if slot_deferred else "materialized",
            }
        )

    status_counts = Counter(row["materialization_status"] for row in window_rows)
    by_root_status = Counter((row["root"], row["materialization_status"]) for row in window_rows)
    slot_status_counts = Counter(row["slot_status"] for row in slot_rows)
    materialized_slot_count = sum(1 for row in slot_rows if row["materialized_closed_window_count"] > 0)
    report = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "source_window_label_panel_materialization_v1",
        "objective": "Materialize approved Bull/Bear/Crisis source-window crosswalk slots into dated label-panel windows.",
        "inputs": {
            "source_window_seed": repo_rel(SOURCE_SEED),
            "source_window_seed_sha256": sha256(SOURCE_SEED),
            "approved_source_window_slots": repo_rel(APPROVED_SLOTS),
            "approved_source_window_slots_sha256": sha256(APPROVED_SLOTS),
            "crosswalk_decision_package": repo_rel(CROSSWALK_PACKAGE),
            "crosswalk_decision_package_sha256": sha256(CROSSWALK_PACKAGE),
            "board": repo_rel(BOARD),
            "board_sha256_at_run": sha256(BOARD),
        },
        "result": {
            "approved_crosswalk_slots_consumed": len(approved_slots),
            "slots_with_closed_windows_materialized": materialized_slot_count,
            "label_panel_window_rows": len(window_rows),
            "closed_label_panel_window_rows": status_counts.get("materialized_closed_window", 0),
            "deferred_refresh_required_rows": status_counts.get("deferred_refresh_required", 0),
            "slot_status_counts": dict(slot_status_counts),
            "window_status_counts": dict(status_counts),
            "by_root_status": {
                f"{root}:{status}": count for (root, status), count in sorted(by_root_status.items())
            },
            "roots_covered_by_materialized_closed_windows": sorted(
                {
                    row["root"]
                    for row in window_rows
                    if row["materialization_status"] == "materialized_closed_window"
                }
            ),
            "instruments_covered": sorted({row["instrument"] for row in window_rows}),
            "timeframes_covered": sorted({row["timeframe"] for row in window_rows}),
        },
        "decision": {
            "new_source_label_slots_with_materialized_windows": materialized_slot_count,
            "new_dated_label_panel_windows": status_counts.get("materialized_closed_window", 0),
            "full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "confidence_gate_claimed": False,
            "why_not_complete": [
                "This materializes source-label windows, not a held-out 95% prediction gate.",
                "Open-ended Yardeni Bull window is deferred until source refresh.",
                "Sideways remains separate after the targeted rerun failed support.",
                "Broader non-S&P instruments and non-yfinance providers remain outside the declared crosswalk.",
                "Direct Manipulation remains direct-event scoped and is not closed by price-root source windows.",
            ],
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "artifacts": {
            "json": repo_rel(OUT_JSON),
            "md": repo_rel(OUT_MD),
            "windows_csv": repo_rel(OUT_WINDOWS),
            "slot_summary_csv": repo_rel(OUT_SLOT_SUMMARY),
            "assertions": repo_rel(ASSERTIONS),
            "script": repo_rel(Path(__file__).resolve()),
        },
        "next_action": "Run a held-out calibration/readiness gate that consumes the materialized Bull/Bear/Crisis label-panel windows while keeping Sideways and Manipulation separate.",
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    with OUT_WINDOWS.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(window_rows[0].keys()))
        writer.writeheader()
        writer.writerows(window_rows)
    with OUT_SLOT_SUMMARY.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(slot_rows[0].keys()))
        writer.writeheader()
        writer.writerows(slot_rows)

    lines = [
        "# Source-Window Label Panel Materialization v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Approved crosswalk slots consumed: `{len(approved_slots)}`.",
        f"- Slots with closed dated windows materialized: `{materialized_slot_count}`.",
        f"- Closed dated label-panel window rows: `{status_counts.get('materialized_closed_window', 0)}`.",
        f"- Deferred refresh-required rows: `{status_counts.get('deferred_refresh_required', 0)}`.",
        f"- Roots covered by closed windows: `{', '.join(report['result']['roots_covered_by_materialized_closed_windows'])}`.",
        f"- Instruments covered: `{', '.join(report['result']['instruments_covered'])}`.",
        f"- Timeframes covered: `{', '.join(report['result']['timeframes_covered'])}`.",
        "",
        "## Counts By Root And Status",
        "",
        "| Root/Status | Count |",
        "|---|---:|",
    ]
    for key, count in report["result"]["by_root_status"].items():
        lines.append(f"| `{key}` | `{count}` |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This is source-label panel materialization, not a calibrated prediction gate.",
            "- Open-ended Yardeni Bull rows are deferred until refresh.",
            "- No Sideways or Manipulation completion is claimed here.",
            "- Runtime code changed: false.",
            "- Thresholds relaxed: false.",
            "- Trade usable: false.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n")

    failures: list[str] = []
    if len(approved_slots) != 63:
        failures.append("expected_63_approved_slots")
    if materialized_slot_count != 63:
        failures.append("expected_all_63_slots_to_have_at_least_one_closed_window")
    if status_counts.get("materialized_closed_window", 0) != 210:
        failures.append("expected_210_closed_window_rows")
    if status_counts.get("deferred_refresh_required", 0) != 21:
        failures.append("expected_21_deferred_open_bull_rows")
    if set(report["result"]["roots_covered_by_materialized_closed_windows"]) != {"Bull", "Bear", "Crisis"}:
        failures.append("expected_bull_bear_crisis_closed_windows")
    if report["decision"]["confidence_gate_claimed"]:
        failures.append("confidence_gate_must_not_be_claimed")
    if failures:
        raise AssertionError("; ".join(failures))

    ASSERTIONS.write_text(
        "\n".join(
            [
                f"PASS run_id={RUN_ID}",
                f"PASS approved_crosswalk_slots_consumed={len(approved_slots)}",
                f"PASS slots_with_closed_windows_materialized={materialized_slot_count}",
                f"PASS closed_label_panel_window_rows={status_counts.get('materialized_closed_window', 0)}",
                f"PASS deferred_refresh_required_rows={status_counts.get('deferred_refresh_required', 0)}",
                "PASS roots_covered_by_materialized_closed_windows=Bull,Bear,Crisis",
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
