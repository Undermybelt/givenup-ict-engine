#!/usr/bin/env python3
"""Check whether the live source-label root can satisfy R3 native sub-hour cells."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path


RUN_ID = "20260512T012000-codex-r3-target-cell-check-against-source-label-root-v1"
REPO = Path(__file__).resolve().parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
OUT_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = OUT_ROOT / "r3-target-cell-check-against-source-label-root-v1"
CHECK_DIR = OUT_ROOT / "checks"

SOURCE_LABEL_ROOT = Path("/tmp/ict-engine-source-label-equivalence-intake")
SOURCE_ROWS = SOURCE_LABEL_ROOT / "source_label_equivalence_rows.csv"
SOURCE_PROVENANCE = SOURCE_LABEL_ROOT / "source_label_equivalence_provenance.json"
R3_NATIVE_ROOT = Path("/tmp/ict-engine-native-subhour-source-label-intake")
R3_NATIVE_ROWS = R3_NATIVE_ROOT / "native_subhour_source_label_rows.csv"
R3_NATIVE_PROVENANCE = R3_NATIVE_ROOT / "native_subhour_source_label_provenance.json"

R3_FOCUS_CSV = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260512T010401-codex-r3-native-subhour-sendable-requests-v2"
    / "r3-native-subhour-sendable-requests-v2/r3_native_subhour_focus_cells_v2.csv"
)

R3_CUTOFF_EXCLUSIVE = date(2026, 1, 30)


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def current_cursor() -> str:
    text = BOARD.read_text()
    marker = "| last_loop_id |"
    for line in text.splitlines():
        if line.startswith(marker):
            parts = [p.strip() for p in line.strip("|").split("|")]
            if len(parts) >= 2:
                return parts[1]
    return "unknown"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    focus_rows = read_csv(R3_FOCUS_CSV)
    source_rows = read_csv(SOURCE_ROWS) if SOURCE_ROWS.exists() else []

    by_symbol: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_symbol_timeframe: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in source_rows:
        symbol = row.get("symbol", "")
        timeframe = row.get("timeframe", "")
        by_symbol[symbol].append(row)
        by_symbol_timeframe[(symbol, timeframe)].append(row)

    target_rows: list[dict[str, object]] = []
    for focus in focus_rows:
        symbol = focus["symbol"]
        timeframe = focus["timeframe"]
        symbol_rows = by_symbol.get(symbol, [])
        exact_rows = by_symbol_timeframe.get((symbol, timeframe), [])
        symbol_dates = [d for d in (parse_date(r.get("timestamp_or_date", "")) for r in symbol_rows) if d]
        exact_dates = [d for d in (parse_date(r.get("timestamp_or_date", "")) for r in exact_rows) if d]
        timeframes_present = sorted({r.get("timeframe", "") for r in symbol_rows if r.get("timeframe")})
        post_cutoff_exact = [d for d in exact_dates if d > R3_CUTOFF_EXCLUSIVE]
        target_rows.append(
            {
                "symbol": symbol,
                "required_timeframe": timeframe,
                "provider_date_min": focus.get("provider_date_min", ""),
                "provider_date_max": focus.get("provider_date_max", ""),
                "source_panel_tail_from_request": focus.get("source_date_max", ""),
                "source_label_rows_total_for_symbol": len(symbol_rows),
                "source_label_timeframes_present": ";".join(timeframes_present),
                "exact_native_timeframe_rows": len(exact_rows),
                "latest_source_label_date_for_symbol": max(symbol_dates).isoformat() if symbol_dates else "",
                "latest_exact_native_timeframe_date": max(exact_dates).isoformat() if exact_dates else "",
                "post_cutoff_exact_native_rows_after_2026_01_30": len(post_cutoff_exact),
                "r3_native_subhour_satisfied": bool(exact_rows and post_cutoff_exact),
                "blocker": "source_label_root_has_daily_rows_only_for_target"
                if symbol_rows and not exact_rows
                else "source_label_root_has_no_symbol_rows",
            }
        )

    all_targets_satisfied = bool(target_rows) and all(
        row["r3_native_subhour_satisfied"] for row in target_rows
    )
    any_exact_native_rows = any(row["exact_native_timeframe_rows"] for row in target_rows)
    gate_result = (
        "r3_target_cell_check_against_source_label_root_v1=source_label_root_has_no_native_subhour_target_rows"
        if not any_exact_native_rows
        else "r3_target_cell_check_against_source_label_root_v1=source_label_root_still_incomplete_for_native_subhour"
    )

    summary = {
        "run_id": RUN_ID,
        "board": str(BOARD.relative_to(REPO)),
        "board_sha256_at_run": sha256(BOARD),
        "current_cursor_observed": current_cursor(),
        "source_label_root": str(SOURCE_LABEL_ROOT),
        "source_label_rows_present": SOURCE_ROWS.exists(),
        "source_label_provenance_present": SOURCE_PROVENANCE.exists(),
        "source_label_rows_sha256": sha256(SOURCE_ROWS),
        "r3_native_root": str(R3_NATIVE_ROOT),
        "r3_native_root_files": sorted(p.name for p in R3_NATIVE_ROOT.glob("*")) if R3_NATIVE_ROOT.exists() else [],
        "r3_required_rows_file_present": R3_NATIVE_ROWS.exists(),
        "r3_required_provenance_file_present": R3_NATIVE_PROVENANCE.exists(),
        "r3_cutoff_exclusive": R3_CUTOFF_EXCLUSIVE.isoformat(),
        "target_rows": target_rows,
        "all_r3_targets_satisfied": all_targets_satisfied,
        "gate_result": gate_result,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "r3_native_root_mutated": False,
        "r6_owner_export_root_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent": False,
        "trade_usable": False,
    }

    fields = [
        "symbol",
        "required_timeframe",
        "provider_date_min",
        "provider_date_max",
        "source_panel_tail_from_request",
        "source_label_rows_total_for_symbol",
        "source_label_timeframes_present",
        "exact_native_timeframe_rows",
        "latest_source_label_date_for_symbol",
        "latest_exact_native_timeframe_date",
        "post_cutoff_exact_native_rows_after_2026_01_30",
        "r3_native_subhour_satisfied",
        "blocker",
    ]
    write_csv(OUT_DIR / "r3_target_cell_source_label_root_check_v1.csv", target_rows, fields)
    (OUT_DIR / "r3_target_cell_check_against_source_label_root_v1.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )

    md_rows = "\n".join(
        "| {symbol} | {required_timeframe} | {source_label_rows_total_for_symbol} | {source_label_timeframes_present} | {exact_native_timeframe_rows} | {latest_source_label_date_for_symbol} | {post_cutoff_exact_native_rows_after_2026_01_30} | {r3_native_subhour_satisfied} |".format(
            **row
        )
        for row in target_rows
    )
    (OUT_DIR / "r3_target_cell_check_against_source_label_root_v1.md").write_text(
        "\n".join(
            [
                "# R3 Target Cell Check Against Source-Label Root v1",
                "",
                f"Run id: `{RUN_ID}`",
                f"Gate result: `{gate_result}`",
                "",
                "This read-only check tests whether the live source-label equivalence root can satisfy the separate R3 native 15m/30m target cells.",
                "",
                "| Symbol | Required Timeframe | Source Rows For Symbol | Source Timeframes Present | Exact Native Rows | Latest Source Date | Post-Cutoff Exact Native Rows | R3 Satisfied |",
                "|---|---:|---:|---|---:|---|---:|---|",
                md_rows,
                "",
                "Result:",
                f"- Source-label root present: `{SOURCE_ROWS.exists() and SOURCE_PROVENANCE.exists()}`.",
                f"- R3 native root present with required files: `{R3_NATIVE_ROWS.exists() and R3_NATIVE_PROVENANCE.exists()}`.",
                f"- All R3 targets satisfied: `{all_targets_satisfied}`.",
                "- The live source-label root contains daily source-panel labels for target symbols, not source-native 15m/30m labels.",
                "- No rows were copied into the R3 root, no thresholds were relaxed, and no downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree promotion was run.",
                "",
                "Next:",
                "- Keep R3 fail-closed until exact native sub-hour source-label rows and provenance arrive under `/tmp/ict-engine-native-subhour-source-label-intake`.",
                "",
            ]
        )
    )

    assertions = {
        "source_label_root_present": SOURCE_ROWS.exists() and SOURCE_PROVENANCE.exists(),
        "r3_native_required_files_absent": not (R3_NATIVE_ROWS.exists() and R3_NATIVE_PROVENANCE.exists()),
        "all_r3_targets_satisfied_false": all_targets_satisfied is False,
        "downstream_chain_rerun_allowed_false": summary["downstream_chain_rerun_allowed"] is False,
        "strict_full_objective_achieved_false": summary["strict_full_objective_achieved"] is False,
    }
    assertion_text = "\n".join(f"{k}={v}" for k, v in assertions.items()) + "\n"
    (CHECK_DIR / "r3_target_cell_check_against_source_label_root_v1_assertions.out").write_text(
        assertion_text
    )
    if not all(assertions.values()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
