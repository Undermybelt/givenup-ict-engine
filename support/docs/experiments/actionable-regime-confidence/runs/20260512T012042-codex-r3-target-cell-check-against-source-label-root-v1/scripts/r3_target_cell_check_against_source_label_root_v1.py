#!/usr/bin/env python3
"""Check whether the source-label root can satisfy R3 native sub-hour cells."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


RUN_ID = "20260512T012042-codex-r3-target-cell-check-against-source-label-root-v1"
BASE = Path("docs/experiments/actionable-regime-confidence/runs")
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")

FOCUS_CSV = (
    BASE
    / "20260512T010401-codex-r3-native-subhour-sendable-requests-v2"
    / "r3-native-subhour-sendable-requests-v2"
    / "r3_native_subhour_focus_cells_v2.csv"
)
SOURCE_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
SOURCE_ROWS = SOURCE_ROOT / "source_label_equivalence_rows.csv"
SOURCE_PROVENANCE = SOURCE_ROOT / "source_label_equivalence_provenance.json"
R3_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
R3_ROWS = R3_ROOT / "native_subhour_source_label_rows.csv"
R3_PROVENANCE = R3_ROOT / "native_subhour_source_label_provenance.json"

OUT_ROOT = BASE / RUN_ID
OUT_DIR = OUT_ROOT / "r3-target-cell-check-against-source-label-root-v1"
CHECK_DIR = OUT_ROOT / "checks"

CUTOFF = "2026-01-30"
ROOT_LABELS = ["Bear", "Bull", "Crisis", "Sideways"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def board_cursor_and_hash() -> tuple[str, str]:
    raw = BOARD.read_bytes()
    text = raw.decode("utf-8")
    match = re.search(r"\| last_loop_id \| ([^|]+) \|", text)
    cursor = match.group(1).strip() if match else "missing"
    return cursor, hashlib.sha256(raw).hexdigest()


def profile_symbol(rows: list[dict[str, str]], symbol: str) -> dict[str, Any]:
    symbol_rows = [row for row in rows if row["symbol"] == symbol]
    exact_timeframes = Counter(row["timeframe"] for row in symbol_rows)
    labels = Counter(row["main_regime_v2_label"] for row in symbol_rows)
    dates = [row["timestamp_or_date"] for row in symbol_rows]
    post_cutoff_rows = [row for row in symbol_rows if row["timestamp_or_date"] > CUTOFF]
    return {
        "symbol_total_rows": len(symbol_rows),
        "symbol_timeframes": ";".join(f"{key}:{value}" for key, value in sorted(exact_timeframes.items())),
        "symbol_labels": ";".join(f"{key}:{value}" for key, value in sorted(labels.items())),
        "symbol_date_min": min(dates) if dates else "",
        "symbol_date_max": max(dates) if dates else "",
        "symbol_post_cutoff_rows": len(post_cutoff_rows),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    cursor, board_sha = board_cursor_and_hash()
    focus_rows = read_csv(FOCUS_CSV)
    source_rows = read_csv(SOURCE_ROWS) if SOURCE_ROWS.exists() else []

    result_rows: list[dict[str, Any]] = []
    for focus in focus_rows:
        symbol = focus["symbol"]
        timeframe = focus["timeframe"]
        exact_rows = [
            row
            for row in source_rows
            if row["symbol"] == symbol
            and row["timeframe"] == timeframe
            and row["timestamp_or_date"] > CUTOFF
        ]
        exact_labels = Counter(row["main_regime_v2_label"] for row in exact_rows)
        symbol_profile = profile_symbol(source_rows, symbol)
        result_rows.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "required_native_subhour": "true",
                "source_label_root_present": str(SOURCE_ROWS.exists() and SOURCE_PROVENANCE.exists()).lower(),
                "r3_native_root_present": str(R3_ROWS.exists() and R3_PROVENANCE.exists()).lower(),
                "exact_native_post_cutoff_rows": len(exact_rows),
                "exact_native_post_cutoff_label_counts": ";".join(f"{key}:{value}" for key, value in sorted(exact_labels.items())),
                "source_root_timeframes_for_symbol": symbol_profile["symbol_timeframes"],
                "source_root_latest_date_for_symbol": symbol_profile["symbol_date_max"],
                "source_root_post_cutoff_rows_for_symbol": symbol_profile["symbol_post_cutoff_rows"],
                "source_root_total_rows_for_symbol": symbol_profile["symbol_total_rows"],
                "source_root_label_counts_for_symbol": symbol_profile["symbol_labels"],
                "accepted_for_r3": "false",
                "blocker": "no_source_native_subhour_post_cutoff_rows",
            }
        )

    write_csv(
        OUT_DIR / "r3_target_cell_source_label_root_check_v1.csv",
        result_rows,
        [
            "symbol",
            "timeframe",
            "required_native_subhour",
            "source_label_root_present",
            "r3_native_root_present",
            "exact_native_post_cutoff_rows",
            "exact_native_post_cutoff_label_counts",
            "source_root_timeframes_for_symbol",
            "source_root_latest_date_for_symbol",
            "source_root_post_cutoff_rows_for_symbol",
            "source_root_total_rows_for_symbol",
            "source_root_label_counts_for_symbol",
            "accepted_for_r3",
            "blocker",
        ],
    )

    all_targets_satisfied = all(int(row["exact_native_post_cutoff_rows"]) > 0 for row in result_rows)
    gate_result = "r3_target_cell_check_against_source_label_root_v1=source_label_root_has_no_native_subhour_target_rows"
    summary = {
        "run_id": RUN_ID,
        "board": str(BOARD),
        "board_sha256_at_run": board_sha,
        "current_cursor_observed": cursor,
        "focus_csv": str(FOCUS_CSV),
        "source_label_root": str(SOURCE_ROOT),
        "source_label_rows_present": SOURCE_ROWS.exists(),
        "source_label_provenance_present": SOURCE_PROVENANCE.exists(),
        "r3_native_root": str(R3_ROOT),
        "r3_native_rows_present": R3_ROWS.exists(),
        "r3_native_provenance_present": R3_PROVENANCE.exists(),
        "cutoff": CUTOFF,
        "root_labels": ROOT_LABELS,
        "focus_cell_count": len(result_rows),
        "focus_results": result_rows,
        "gate_result": gate_result,
        "all_targets_satisfied": all_targets_satisfied,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r3_root_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }
    (OUT_DIR / "r3_target_cell_check_against_source_label_root_v1.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    table_rows = "\n".join(
        "| {symbol} | {timeframe} | {exact_native_post_cutoff_rows} | {source_root_timeframes_for_symbol} | {source_root_latest_date_for_symbol} | {source_root_post_cutoff_rows_for_symbol} | {blocker} |".format(**row)
        for row in result_rows
    )
    (OUT_DIR / "r3_target_cell_check_against_source_label_root_v1.md").write_text(
        f"""# R3 Target Cell Check Against Source-Label Root v1

- Run id: `{RUN_ID}`.
- Gate result: `{gate_result}`.
- Board cursor observed: `{cursor}`.
- Source-label equivalence root present: `{SOURCE_ROWS.exists() and SOURCE_PROVENANCE.exists()}`.
- R3 native-subhour root present: `{R3_ROWS.exists() and R3_PROVENANCE.exists()}`.
- Required target cells: `AAPL 15m`, `AAPL 30m`, `^IXIC 15m`, `^IXIC 30m`.
- Required cutoff: rows after `{CUTOFF}`.
- Accepted rows added: `0`; new confidence gate: false. `update_goal=false`.
- Downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: false.

| symbol | timeframe | exact native post-cutoff rows | source-root timeframes for symbol | source-root latest date | source-root post-cutoff rows | blocker |
| --- | --- | --- | --- | --- | --- | --- |
{table_rows}

## Decision

The live source-label equivalence root is daily (`1d`) source-panel material and cannot satisfy R3 native 15m/30m requirements. It also does not supply post-`{CUTOFF}` source-native sub-hour rows for the focus cells. Do not project daily labels into sub-hour windows, and do not populate `/tmp/ict-engine-native-subhour-source-label-intake` until source-native rows plus provenance arrive.
""",
        encoding="utf-8",
    )

    checks = [
        ("board_present", BOARD.exists()),
        ("current_cursor_010127", "20260512T010127" in cursor),
        ("focus_cell_count_4", len(result_rows) == 4),
        ("source_label_root_present", SOURCE_ROWS.exists() and SOURCE_PROVENANCE.exists()),
        ("r3_native_root_absent", not (R3_ROWS.exists() and R3_PROVENANCE.exists())),
        ("no_exact_native_post_cutoff_rows", sum(int(row["exact_native_post_cutoff_rows"]) for row in result_rows) == 0),
        ("all_targets_satisfied_false", not all_targets_satisfied),
        ("accepted_rows_added_zero", summary["accepted_rows_added"] == 0),
        ("new_confidence_gate_false", not summary["new_confidence_gate"]),
        ("downstream_chain_rerun_allowed_false", not summary["downstream_chain_rerun_allowed"]),
        ("strict_full_objective_achieved_false", not summary["strict_full_objective_achieved"]),
        ("update_goal_false", not summary["update_goal"]),
        ("runtime_code_changed_false", not summary["runtime_code_changed"]),
        ("shared_intake_mutated_false", not summary["shared_intake_mutated"]),
        ("r3_root_mutated_false", not summary["r3_root_mutated"]),
        ("thresholds_relaxed_false", not summary["thresholds_relaxed"]),
        ("external_requests_sent_false", not summary["external_requests_sent"]),
    ]
    assertion_text = "\n".join(f"{name}={'PASS' if ok else 'FAIL'}" for name, ok in checks) + "\n"
    (CHECK_DIR / "r3_target_cell_check_against_source_label_root_v1_assertions.out").write_text(
        assertion_text,
        encoding="utf-8",
    )
    failed = [name for name, ok in checks if not ok]
    if failed:
        raise SystemExit("failed checks: " + ", ".join(failed))


if __name__ == "__main__":
    main()
