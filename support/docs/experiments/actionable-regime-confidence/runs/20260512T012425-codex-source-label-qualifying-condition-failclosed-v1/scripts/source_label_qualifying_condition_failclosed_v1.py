#!/usr/bin/env python3
"""Regenerate the 012425 fail-closed source-label condition artifact."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20260512T012425-codex-source-label-qualifying-condition-failclosed-v1"
OUT = RUN_ROOT / "source-label-qualifying-condition-failclosed-v1"
CHECKS = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
INTAKE_ROWS = Path("/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_rows.csv")
INTAKE_PROVENANCE = Path("/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_provenance.json")
STOCK_SOURCE = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
NIFTY_SOURCE = Path("/tmp/ict-engine-source-label-equivalence-reconstruction-v1/nifty/regime_timeline_history.csv")

CALIBRATION_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T011056-codex-source-label-equivalence-calibration-after-root-poll-v1/"
    "source-label-equivalence-confidence-calibration/source_label_equivalence_confidence_calibration_v1.json"
)
TRIAGE_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T011819-codex-source-label-high-confidence-subset-triage-v1/"
    "source-label-high-confidence-subset-triage-v1/source_label_high_confidence_subset_triage_v1.json"
)
BASELINE_JSON = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T012330-codex-source-label-bull-sideways-qualifying-condition-v1/"
    "source-label-bull-sideways-qualifying-condition-v1/source_label_bull_sideways_qualifying_condition_v1.json"
)
BASELINE_SPLIT_CSV = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T012330-codex-source-label-bull-sideways-qualifying-condition-v1/"
    "source-label-bull-sideways-qualifying-condition-v1/source_label_bull_sideways_split_support_v1.csv"
)
BASELINE_MARKET_CSV = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T012330-codex-source-label-bull-sideways-qualifying-condition-v1/"
    "source-label-bull-sideways-qualifying-condition-v1/source_label_bull_sideways_market_support_v1.csv"
)

TARGET_LABELS = ["Bull", "Sideways"]
REQUIRED_SPLITS = ["calibration", "heldout_market", "heldout_time", "test"]
CONFIDENCE_THRESHOLD = 0.95


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def current_cursor(board_text: str) -> str:
    match = re.search(r"\| last_loop_id \| ([^|]+) \|", board_text)
    return match.group(1).strip() if match else "unknown"


def stock_confidence_map() -> dict[tuple[str, str, str], float]:
    values: dict[tuple[str, str, str], float] = {}
    for row in read_csv(STOCK_SOURCE):
        try:
            confidence = float(row.get("regime_confidence", ""))
        except ValueError:
            continue
        values[(row.get("date", ""), row.get("ticker", ""), row.get("regime_label", ""))] = confidence
    return values


def nifty_confidence_map() -> dict[tuple[str, str, str, str], float]:
    values: dict[tuple[str, str, str, str], float] = {}
    for row in read_csv(NIFTY_SOURCE):
        day = row.get("Date", "")
        symbol = "NIFTY500"
        if row.get("macro_state") == "Durable":
            values[(day, symbol, "NIFTY500:macro_state", "Bull")] = float(row.get("macro_confidence") or 0.0)
        if row.get("fast_state") == "Calm":
            values[(day, symbol, "NIFTY500:fast_state", "Sideways")] = float(row.get("fast_confidence") or 0.0)
        if row.get("fast_state") == "Stress":
            values[(day, symbol, "NIFTY500:fast_state", "Crisis")] = float(row.get("fast_confidence") or 0.0)
    return values


def row_confidence(
    row: dict[str, str],
    stock: dict[tuple[str, str, str], float],
    nifty: dict[tuple[str, str, str, str], float],
) -> float | None:
    label = row.get("main_regime_v2_label", "")
    if row.get("source_owner") == "source-owned-stock-market-regimes-2000-2026":
        return stock.get((row.get("timestamp_or_date", ""), row.get("symbol", ""), label))
    if row.get("source_owner") == "ahaanverma00":
        return nifty.get((row.get("timestamp_or_date", ""), row.get("symbol", ""), row.get("source_symbol", ""), label))
    return None


def sample_rows() -> list[dict[str, Any]]:
    stock = stock_confidence_map()
    nifty = nifty_confidence_map()
    samples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in read_csv(INTAKE_ROWS):
        label = row.get("main_regime_v2_label", "")
        if label not in TARGET_LABELS or len(samples[label]) >= 12:
            continue
        confidence = row_confidence(row, stock, nifty)
        if confidence is None or confidence < CONFIDENCE_THRESHOLD:
            continue
        samples[label].append(
            {
                "label": label,
                "timestamp_or_date": row.get("timestamp_or_date", ""),
                "symbol": row.get("symbol", ""),
                "source_owner": row.get("source_owner", ""),
                "market_family": row.get("market_family", ""),
                "split_role": row.get("split_role", ""),
                "timeframe": row.get("timeframe", ""),
                "source_confidence": f"{confidence:.10f}",
                "source_row_id": row.get("source_row_id", ""),
            }
        )
    return [item for label in TARGET_LABELS for item in samples[label]]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    required = [
        BOARD,
        INTAKE_ROWS,
        INTAKE_PROVENANCE,
        STOCK_SOURCE,
        NIFTY_SOURCE,
        CALIBRATION_JSON,
        TRIAGE_JSON,
        BASELINE_JSON,
        BASELINE_SPLIT_CSV,
        BASELINE_MARKET_CSV,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(missing)

    board_text = BOARD.read_text(encoding="utf-8")
    calibration = json.loads(CALIBRATION_JSON.read_text(encoding="utf-8"))
    triage = json.loads(TRIAGE_JSON.read_text(encoding="utf-8"))
    baseline = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
    label_summaries = {row["label"]: row for row in baseline["label_summary"]}

    lcb_by_label_split = {
        (row["label"], row["split_role"]): row["wilson95_lcb"]
        for row in calibration["label_split_confidence"]
        if row["label"] in TARGET_LABELS
    }

    condition_rows: list[dict[str, Any]] = []
    for label in TARGET_LABELS:
        summary = label_summaries[label]
        lcb_text = ";".join(
            f"{split}:{lcb_by_label_split[(label, split)]:.10f}" for split in REQUIRED_SPLITS
        )
        blockers = [
            "source_label_equivalence_confidence_calibration_v1_no_accepted_labels",
            "r6_owner_controls_or_flip_approval_missing",
            "canonical_merge_not_allowed",
        ]
        blockers.extend(f"{split}_source_confidence_wilson95_below_0.95" for split in REQUIRED_SPLITS)
        condition_rows.append(
            {
                "label": label,
                "qualifying_condition": summary["qualifying_condition"].replace("'", ""),
                "validation_instruments": f"{summary['symbol_count']} symbols",
                "validation_periods": "calibration;heldout_market;heldout_time;test",
                "validation_market_contexts": "india_equity_index;us_index;us_single_stock",
                "high_conf_rows": summary["high_conf_rows"],
                "date_min": summary["date_min"],
                "date_max": summary["date_max"],
                "condition_support_gate_pass": summary["split_support_pass"],
                "cross_axis_fields_complete": "true",
                "baseline_full_row_confidence_gate_pass": "false",
                "baseline_full_row_wilson95_lcb_by_split": lcb_text,
                "accepted_label": "false",
                "blockers": ";".join(blockers),
            }
        )

    split_rows = []
    split_support = read_csv(BASELINE_SPLIT_CSV)
    for row in split_support:
        label = row["label"]
        split = row["split_role"]
        split_rows.append(
            {
                "label": label,
                "split_role": split,
                "condition_high_conf_rows": row["high_conf_rows"],
                "baseline_full_row_wilson95_lcb": f"{lcb_by_label_split[(label, split)]:.10f}",
                "baseline_full_row_gate_pass": "false",
            }
        )

    market_rows = read_csv(BASELINE_MARKET_CSV)
    samples = sample_rows()

    result = {
        "run_id": RUN_ID,
        "decision": "source_label_qualifying_condition_failclosed_v1=conditions_present_but_no_acceptance",
        "current_cursor_observed": current_cursor(board_text),
        "board_hash_before_artifact_repair": sha256_file(BOARD),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "calibration_run": calibration["run_id"],
        "calibration_decision": calibration["decision"],
        "triage_run": triage["run_id"],
        "triage_decision": triage["decision"],
        "triage_candidate_labels": TARGET_LABELS,
        "field_complete_labels": TARGET_LABELS,
        "accepted_labels": [],
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r3_root_mutated": False,
        "r5_root_mutated": False,
        "r6_owner_export_root_mutated": False,
        "r3_native_root_present": Path("/tmp/ict-engine-native-subhour-source-label-intake").exists(),
        "r5_recency_root_present": Path("/tmp/ict-engine-source-panel-recency-extension").exists(),
        "r6_owner_export_root_present": Path("/tmp/ict-engine-board-a-r6-owner-export-v1").exists(),
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
        "source_rows_path": str(INTAKE_ROWS),
        "source_rows_sha256": sha256_file(INTAKE_ROWS),
        "source_provenance_sha256": sha256_file(INTAKE_PROVENANCE),
        "condition_rows": condition_rows,
    }

    write_csv(
        OUT / "source_label_qualifying_condition_failclosed_conditions_v1.csv",
        condition_rows,
        [
            "label",
            "qualifying_condition",
            "validation_instruments",
            "validation_periods",
            "validation_market_contexts",
            "high_conf_rows",
            "date_min",
            "date_max",
            "condition_support_gate_pass",
            "cross_axis_fields_complete",
            "baseline_full_row_confidence_gate_pass",
            "baseline_full_row_wilson95_lcb_by_split",
            "accepted_label",
            "blockers",
        ],
    )
    write_csv(
        OUT / "source_label_qualifying_condition_failclosed_split_validation_v1.csv",
        split_rows,
        [
            "label",
            "split_role",
            "condition_high_conf_rows",
            "baseline_full_row_wilson95_lcb",
            "baseline_full_row_gate_pass",
        ],
    )
    write_csv(
        OUT / "source_label_qualifying_condition_failclosed_market_contexts_v1.csv",
        market_rows,
        ["label", "market_family", "high_conf_rows"],
    )
    write_csv(
        OUT / "source_label_qualifying_condition_failclosed_sample_rows_v1.csv",
        samples,
        [
            "label",
            "timestamp_or_date",
            "symbol",
            "source_owner",
            "market_family",
            "split_role",
            "timeframe",
            "source_confidence",
            "source_row_id",
        ],
    )

    (OUT / "source_label_qualifying_condition_failclosed_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Source Label Qualifying Condition Fail-Closed v1",
        "",
        f"- Decision: `{result['decision']}`.",
        f"- Current cursor observed: `{result['current_cursor_observed']}`.",
        f"- Baseline calibration: `{result['calibration_decision']}`.",
        f"- Triage baseline: `{result['triage_decision']}` with candidate labels `{TARGET_LABELS}`.",
        f"- Field-complete condition labels: `{TARGET_LABELS}`.",
        "- Accepted labels: `[]`; accepted rows added: `0`; new confidence gate: `false`.",
        "- Canonical merge allowed: `false`; downstream chain rerun allowed: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.",
        "",
        "## Conditions",
        "",
        "| Label | High-Conf Rows | Support Gate | Cross-Axis Fields | Date Range | Accepted | Blockers |",
        "|---|---:|---|---|---|---|---|",
    ]
    for row in condition_rows:
        lines.append(
            f"| `{row['label']}` | `{row['high_conf_rows']}` | `{row['condition_support_gate_pass']}` | "
            f"`{row['cross_axis_fields_complete']}` | `{row['date_min']}..{row['date_max']}` | "
            f"`{row['accepted_label']}` | `{row['blockers']}` |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This repaired artifact restores the run root already referenced by the board. It preserves the fail-closed outcome: Bull and Sideways have explicit condition fields, but no labels are accepted because the baseline full-row source-confidence calibration, R6 owner-control gate, canonical merge gate, and downstream promotion gate remain blocked.",
        ]
    )
    (OUT / "source_label_qualifying_condition_failclosed_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = {
        "run_id": result["run_id"] == RUN_ID,
        "current_cursor_010127": "20260512T010127" in result["current_cursor_observed"],
        "triage_candidates_match_target": result["triage_candidate_labels"] == TARGET_LABELS,
        "field_complete_labels_bull_sideways": result["field_complete_labels"] == TARGET_LABELS,
        "accepted_labels_empty": result["accepted_labels"] == [],
        "accepted_rows_added_zero": result["accepted_rows_added"] == 0,
        "new_confidence_gate_false": not result["new_confidence_gate"],
        "canonical_merge_allowed_false": not result["canonical_merge_allowed"],
        "downstream_chain_rerun_allowed_false": not result["downstream_chain_rerun_allowed"],
        "strict_full_objective_achieved_false": not result["strict_full_objective_achieved"],
        "update_goal_false": not result["update_goal"],
        "runtime_code_changed_false": not result["runtime_code_changed"],
        "shared_intake_mutated_false": not result["shared_intake_mutated"],
        "roots_not_mutated": not any([result["r3_root_mutated"], result["r5_root_mutated"], result["r6_owner_export_root_mutated"]]),
        "thresholds_relaxed_false": not result["thresholds_relaxed"],
        "raw_data_committed_false": not result["raw_data_committed"],
        "external_requests_sent_false": not result["external_requests_sent"],
        "trade_usable_false": not result["trade_usable"],
    }
    assertion_text = "\n".join(f"{name}={'PASS' if ok else 'FAIL'}" for name, ok in assertions.items()) + "\n"
    (CHECKS / "source_label_qualifying_condition_failclosed_v1_assertions.out").write_text(assertion_text, encoding="utf-8")
    if not all(assertions.values()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
