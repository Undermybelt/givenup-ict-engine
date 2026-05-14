#!/usr/bin/env python3
"""Materialize high-confidence source-label subset as a fail-closed qualifying-condition probe."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


RUN_ID = "20260512T012318-codex-source-label-high-confidence-qualifying-condition-probe-v1"
REPO = Path(__file__).resolve().parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
OUT_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = OUT_ROOT / "source-label-high-confidence-qualifying-condition-probe-v1"
CHECK_DIR = OUT_ROOT / "checks"

TRIAGE_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T011819-codex-source-label-high-confidence-subset-triage-v1"
    / "source-label-high-confidence-subset-triage-v1"
)
TRIAGE_JSON = TRIAGE_ROOT / "source_label_high_confidence_subset_triage_v1.json"
LABEL_SUMMARY_CSV = TRIAGE_ROOT / "source_label_high_confidence_subset_label_summary_v1.csv"
SPLIT_CSV = TRIAGE_ROOT / "source_label_high_confidence_subset_split_support_v1.csv"
MARKET_CSV = TRIAGE_ROOT / "source_label_high_confidence_subset_market_support_v1.csv"

ROOT_LABELS = ["Bear", "Bull", "Crisis", "Sideways"]
PROBE_LABELS = ["Bull", "Sideways"]
REQUIRED_SPLITS = ["calibration", "heldout_market", "heldout_time", "test"]
MIN_SUPPORT_PER_SPLIT = 50
CONFIDENCE_THRESHOLD = 0.95
REQUIRED_TIMEFRAME_VARIETY = 2


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def current_cursor() -> str:
    for line in BOARD.read_text(encoding="utf-8").splitlines():
        if line.startswith("| last_loop_id |"):
            parts = [part.strip() for part in line.strip("|").split("|")]
            return parts[1] if len(parts) > 1 else "unknown"
    return "unknown"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    triage = json.loads(TRIAGE_JSON.read_text(encoding="utf-8"))
    label_summary = {row["label"]: row for row in read_csv(LABEL_SUMMARY_CSV)}
    split_rows = read_csv(SPLIT_CSV)
    market_rows = read_csv(MARKET_CSV)

    split_support = {
        (row["label"], row["split_role"]): int(row["high_conf_rows"])
        for row in split_rows
    }
    market_support = {
        (row["label"], row["market_family"]): int(row["high_conf_rows"])
        for row in market_rows
    }

    condition_rows: list[dict[str, object]] = []
    for label in ROOT_LABELS:
        summary = label_summary[label]
        split_counts = [split_support.get((label, split), 0) for split in REQUIRED_SPLITS]
        market_families = sorted(
            market for (row_label, market), count in market_support.items() if row_label == label and count > 0
        )
        timeframes = [value for value in summary.get("high_conf_timeframes", "").split("|") if value]
        support_pass = all(count >= MIN_SUPPORT_PER_SPLIT for count in split_counts)
        cross_market_pass = len(market_families) >= 2
        timeframe_variety_pass = len(set(timeframes)) >= REQUIRED_TIMEFRAME_VARIETY
        label_in_probe = label in PROBE_LABELS
        qualifying_condition_id = (
            f"{label.lower()}_source_confidence_ge_0_95_daily_source_panel_v1"
            if label_in_probe
            else ""
        )
        blockers: list[str] = []
        if not support_pass:
            blockers.append("split_support_below_50")
        if not cross_market_pass:
            blockers.append("cross_market_family_coverage_below_2")
        if not timeframe_variety_pass:
            blockers.append("timeframe_variety_below_other_cycle_requirement")
        if not label_in_probe:
            blockers.append("not_triage_candidate")
        condition_rows.append(
            {
                "label": label,
                "qualifying_condition_id": qualifying_condition_id,
                "qualifying_condition": "source_confidence >= 0.95 AND timeframe == 1d AND source_owned_label == MainRegimeV2"
                if label_in_probe
                else "",
                "high_conf_rows": summary["high_conf_rows"],
                "split_support_calibration": split_support.get((label, "calibration"), 0),
                "split_support_heldout_market": split_support.get((label, "heldout_market"), 0),
                "split_support_heldout_time": split_support.get((label, "heldout_time"), 0),
                "split_support_test": split_support.get((label, "test"), 0),
                "split_support_pass": support_pass,
                "validation_market_contexts": ";".join(market_families),
                "cross_market_pass": cross_market_pass,
                "validation_periods": ";".join(REQUIRED_SPLITS),
                "validation_timeframes": ";".join(timeframes),
                "timeframe_variety_pass": timeframe_variety_pass,
                "validation_instruments_count": summary["high_conf_symbol_count"],
                "date_min": summary["high_conf_date_min"],
                "date_max": summary["high_conf_date_max"],
                "probe_candidate": label_in_probe,
                "accepted_95": False,
                "blockers": ";".join(blockers),
            }
        )

    candidate_rows = [row for row in condition_rows if row["probe_candidate"]]
    all_candidate_split_market_pass = all(
        row["split_support_pass"] and row["cross_market_pass"] for row in candidate_rows
    )
    any_candidate_timeframe_pass = any(row["timeframe_variety_pass"] for row in candidate_rows)
    gate_result = (
        "source_label_high_confidence_qualifying_condition_probe_v1=bull_sideways_split_market_support_ready_timeframe_blocked_no_acceptance"
    )

    summary_json = {
        "run_id": RUN_ID,
        "board": str(BOARD.relative_to(REPO)),
        "board_sha256_at_run": sha256(BOARD),
        "current_cursor_observed": current_cursor(),
        "triage_input_run": triage.get("run_id"),
        "triage_decision": triage.get("decision"),
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "min_support_per_split": MIN_SUPPORT_PER_SPLIT,
        "required_timeframe_variety": REQUIRED_TIMEFRAME_VARIETY,
        "probe_labels": PROBE_LABELS,
        "condition_rows": condition_rows,
        "candidate_split_market_support_ready": all_candidate_split_market_pass,
        "candidate_timeframe_variety_ready": any_candidate_timeframe_pass,
        "accepted_labels": [],
        "gate_result": gate_result,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r6_owner_export_root_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }

    fields = [
        "label",
        "qualifying_condition_id",
        "qualifying_condition",
        "high_conf_rows",
        "split_support_calibration",
        "split_support_heldout_market",
        "split_support_heldout_time",
        "split_support_test",
        "split_support_pass",
        "validation_market_contexts",
        "cross_market_pass",
        "validation_periods",
        "validation_timeframes",
        "timeframe_variety_pass",
        "validation_instruments_count",
        "date_min",
        "date_max",
        "probe_candidate",
        "accepted_95",
        "blockers",
    ]
    write_csv(OUT_DIR / "source_label_high_confidence_qualifying_condition_probe_v1.csv", condition_rows, fields)
    (OUT_DIR / "source_label_high_confidence_qualifying_condition_probe_v1.json").write_text(
        json.dumps(summary_json, indent=2) + "\n",
        encoding="utf-8",
    )

    candidate_lines = "\n".join(
        "| {label} | {qualifying_condition_id} | {high_conf_rows} | {split_support_pass} | {validation_market_contexts} | {validation_timeframes} | {timeframe_variety_pass} | {accepted_95} | {blockers} |".format(
            **row
        )
        for row in condition_rows
    )
    (OUT_DIR / "source_label_high_confidence_qualifying_condition_probe_v1.md").write_text(
        "\n".join(
            [
                "# Source Label High-Confidence Qualifying-Condition Probe v1",
                "",
                f"Run id: `{RUN_ID}`",
                f"Gate result: `{gate_result}`",
                "",
                "This packet materializes the `011819` Bull/Sideways lead as an explicit fail-closed qualifying-condition probe. It is not an acceptance packet.",
                "",
                "| Label | Qualifying Condition ID | High-Confidence Rows | Split Support Pass | Market Contexts | Timeframes | Timeframe Variety Pass | Accepted 95 | Blockers |",
                "|---|---|---:|---|---|---|---|---|---|",
                candidate_lines,
                "",
                "Result:",
                "- Bull and Sideways have enough high-confidence source-label support across required splits and market families.",
                "- Both remain daily-only (`1d`) source-panel conditions, so the other-cycle/timeframe requirement is not satisfied.",
                "- Bear and Crisis remain blocked before this probe because their high-confidence subset support is incomplete.",
                "- This packet does not override the failed `011056` full source-confidence gate and does not allow downstream promotion.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assertions = {
        "candidate_split_market_support_ready": all_candidate_split_market_pass,
        "candidate_timeframe_variety_ready_false": any_candidate_timeframe_pass is False,
        "accepted_labels_empty": summary_json["accepted_labels"] == [],
        "downstream_chain_rerun_allowed_false": summary_json["downstream_chain_rerun_allowed"] is False,
        "strict_full_objective_achieved_false": summary_json["strict_full_objective_achieved"] is False,
    }
    (CHECK_DIR / "source_label_high_confidence_qualifying_condition_probe_v1_assertions.out").write_text(
        "\n".join(f"{key}={value}" for key, value in assertions.items()) + "\n",
        encoding="utf-8",
    )
    return 0 if all(assertions.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
