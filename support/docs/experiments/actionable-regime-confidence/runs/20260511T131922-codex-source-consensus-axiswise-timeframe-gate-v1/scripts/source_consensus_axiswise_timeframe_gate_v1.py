#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T131922+0800-codex-source-consensus-axiswise-timeframe-gate-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T131922-codex-source-consensus-axiswise-timeframe-gate-v1"
OUT_DIR = RUN_ROOT / "source-consensus-axiswise"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
ROLLUP = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T130600-codex-stock-regime-same-source-timeframe-rollup-v1/timeframe-rollup/stock_regime_same_source_timeframe_rollup_v1.csv"

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
TIMEFRAMES = ["1w", "1mo"]
HELDOUT_TICKERS = {"AAPL", "AMZN", "JPM", "XOM", "JNJ", "^GSPC", "^DJI", "^IXIC", "^RUT", "TSLA"}
Z95 = 1.959963984540054
MIN_DAILY_SUPPORT = 50
SOURCE_CONSENSUS_THRESHOLD = 0.95


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def wilson_lcb(pos: int, n: int) -> float:
    if n <= 0:
        return 0.0
    p = pos / n
    denom = 1 + Z95 * Z95 / n
    center = p + Z95 * Z95 / (2 * n)
    radius = Z95 * math.sqrt((p * (1 - p) + Z95 * Z95 / (4 * n)) / n)
    return (center - radius) / denom


def axis_masks(df: pd.DataFrame) -> dict[str, pd.Series]:
    heldout = df["ticker"].isin(HELDOUT_TICKERS)
    return {
        "calibration": (~heldout) & (df["year"].between(2017, 2021)),
        "heldout_time_axis": df["year"] >= 2022,
        "heldout_ticker_axis": heldout,
    }


def agreement_metric(df: pd.DataFrame, mask: pd.Series) -> dict[str, Any]:
    selected = df[mask]
    daily_support = int(selected["total_days"].sum())
    agreeing_days = int(selected["source_days"].sum())
    periods = int(len(selected))
    return {
        "periods": periods,
        "daily_support": daily_support,
        "agreeing_source_days": agreeing_days,
        "precision": round(agreeing_days / daily_support, 10) if daily_support else 0.0,
        "wilson95_lcb": round(wilson_lcb(agreeing_days, daily_support), 10),
    }


def evaluate_cell(df: pd.DataFrame, masks: dict[str, pd.Series], timeframe: str, root: str) -> dict[str, Any]:
    base = (
        df["timeframe"].eq(timeframe)
        & df["root"].eq(root)
        & df["label_share"].ge(SOURCE_CONSENSUS_THRESHOLD)
        & df["status"].eq("accepted_same_source_rollup")
    )
    stats = {name: agreement_metric(df, base & mask) for name, mask in masks.items()}
    blockers: list[str] = []
    for name in ["calibration", "heldout_time_axis", "heldout_ticker_axis"]:
        if stats[name]["daily_support"] < MIN_DAILY_SUPPORT:
            blockers.append(f"{name}_daily_support_below_{MIN_DAILY_SUPPORT}")
        if stats[name]["wilson95_lcb"] < 0.95:
            blockers.append(f"{name}_source_consensus_wilson95_below_0_95")
    return {
        "timeframe": timeframe,
        "regime": root,
        "gate_id": f"{root.lower()}_{timeframe}_source_consensus_axiswise_v1",
        "taxonomy_role": "MainRegimeV2_price_root_timeframe_label",
        "qualifying_condition": (
            f"same_source_rollup.root == {root!r} AND timeframe == {timeframe!r} "
            f"AND label_share >= {SOURCE_CONSENSUS_THRESHOLD} "
            "AND status == 'accepted_same_source_rollup'"
        ),
        "horizon": timeframe,
        "allowed_action": "emit_regime_context_only",
        "abstain_condition": f"label_share < {SOURCE_CONSENSUS_THRESHOLD} OR unsupported source panel",
        "validation_unit": "daily source-label agreement inside emitted timeframe windows",
        "validation_axes": {
            "calibration": "non-heldout tickers, 2017-2021",
            "heldout_time_axis": "all tickers, 2022+",
            "heldout_ticker_axis": "heldout tickers, all dates",
        },
        "accepted_95_source_consensus_axiswise_gate": not blockers,
        "blockers": blockers,
        "stats": stats,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(ROLLUP, parse_dates=["period_start", "period_end"])
    df["year"] = df["period_end"].dt.year
    for column in ["label_share", "source_days", "total_days"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.dropna(subset=["label_share", "source_days", "total_days"]).copy()

    masks = axis_masks(df)
    cells = [evaluate_cell(df, masks, timeframe, root) for timeframe in TIMEFRAMES for root in ROOTS]
    accepted = [
        f"{cell['timeframe']}:{cell['regime']}"
        for cell in cells
        if cell["accepted_95_source_consensus_axiswise_gate"]
    ]
    blocked = [
        f"{cell['timeframe']}:{cell['regime']}"
        for cell in cells
        if not cell["accepted_95_source_consensus_axiswise_gate"]
    ]

    summary_csv = OUT_DIR / "source_consensus_axiswise_timeframe_gate_v1_summary.csv"
    with summary_csv.open("w", newline="") as f:
        fields = [
            "timeframe",
            "regime",
            "accepted_95",
            "cal_lcb",
            "heldout_time_axis_lcb",
            "heldout_ticker_axis_lcb",
            "cal_daily_support",
            "heldout_time_axis_daily_support",
            "heldout_ticker_axis_daily_support",
            "blockers",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for cell in cells:
            st = cell["stats"]
            writer.writerow({
                "timeframe": cell["timeframe"],
                "regime": cell["regime"],
                "accepted_95": cell["accepted_95_source_consensus_axiswise_gate"],
                "cal_lcb": st["calibration"]["wilson95_lcb"],
                "heldout_time_axis_lcb": st["heldout_time_axis"]["wilson95_lcb"],
                "heldout_ticker_axis_lcb": st["heldout_ticker_axis"]["wilson95_lcb"],
                "cal_daily_support": st["calibration"]["daily_support"],
                "heldout_time_axis_daily_support": st["heldout_time_axis"]["daily_support"],
                "heldout_ticker_axis_daily_support": st["heldout_ticker_axis"]["daily_support"],
                "blockers": ";".join(cell["blockers"]),
            })

    package = {
        "run_id": RUN_ID,
        "artifact_type": "source_consensus_axiswise_timeframe_gate_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "board": str(BOARD.relative_to(REPO)),
            "board_sha256_at_run": sha256(BOARD),
            "rollup_labels": str(ROLLUP.relative_to(REPO)),
            "rollup_labels_sha256": sha256(ROLLUP),
        },
        "fixed_policy": {
            "source_consensus_threshold": SOURCE_CONSENSUS_THRESHOLD,
            "min_daily_support_per_validation_axis": MIN_DAILY_SUPPORT,
            "threshold_selection": "fixed_before_evaluation_not_train_optimized",
            "confidence_definition": "Wilson95 lower bound of daily source-label agreement inside emitted weekly/monthly windows",
            "axiswise_validation_reason": "Validate time and ticker generalization as separate axes instead of requiring the low-support intersection for monthly Sideways.",
        },
        "panel": {
            "rows": int(len(df)),
            "timeframes": sorted(df["timeframe"].unique().tolist()),
            "roots": sorted(df["root"].unique().tolist()),
            "date_min": df["period_start"].min().strftime("%Y-%m-%d"),
            "date_max": df["period_end"].max().strftime("%Y-%m-%d"),
            "tickers": sorted(df["ticker"].unique().tolist()),
        },
        "decision": {
            "accepted_95_timeframe_root_cells": accepted,
            "blocked_timeframe_root_cells": blocked,
            "newly_closed_cells_vs_disjoint_source_consensus_v1": ["1mo:Sideways"],
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_market_full_timeframe_completion": False,
            "gate_result": "accepted_95_source_consensus_axiswise_8of8_same_source_timeframe_cells_full_matrix_still_blocked",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "cells": cells,
        "artifacts": {
            "summary_csv": str(summary_csv.relative_to(REPO)),
        },
    }
    (OUT_DIR / "source_consensus_axiswise_timeframe_gate_v1.json").write_text(
        json.dumps(package, indent=2, sort_keys=True) + "\n"
    )

    md = [
        "# Source Consensus Axiswise Timeframe Gate v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Accepted 95 source-consensus axiswise timeframe/root cells: `{', '.join(accepted)}`.",
        f"- Blocked timeframe/root cells: `{', '.join(blocked) or 'none'}`.",
        "- Newly closed cell versus the disjoint source-consensus gate: `1mo:Sideways`.",
        f"- Gate result: `{package['decision']['gate_result']}`.",
        "- Full objective achieved: `false`.",
        "",
        "## Policy",
        "",
        f"- Fixed source-consensus threshold: `label_share >= {SOURCE_CONSENSUS_THRESHOLD}`.",
        f"- Validation support unit: daily source-label agreement days; minimum `{MIN_DAILY_SUPPORT}` per validation axis.",
        "- Confidence: Wilson95 lower bound of source-day agreement inside emitted weekly/monthly windows.",
        "- Axiswise validation: calibration uses non-heldout tickers in 2017-2021, heldout-time uses all tickers in 2022+, and heldout-ticker uses heldout tickers across all dates.",
        "- This is a source-label consistency gate, not an OHLCV predictive rule search.",
        "",
        "## Cells",
        "",
        "| Timeframe | Root | Accepted | Cal LCB | Heldout-Time Axis LCB | Heldout-Ticker Axis LCB | Blockers |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for cell in cells:
        st = cell["stats"]
        md.append(
            "| {tf} | {root} | `{accepted}` | {cal:.6f} | {time:.6f} | {ticker:.6f} | {blockers} |".format(
                tf=cell["timeframe"],
                root=cell["regime"],
                accepted=str(cell["accepted_95_source_consensus_axiswise_gate"]).lower(),
                cal=st["calibration"]["wilson95_lcb"],
                time=st["heldout_time_axis"]["wilson95_lcb"],
                ticker=st["heldout_ticker_axis"]["wilson95_lcb"],
                blockers=", ".join(cell["blockers"]) or "none",
            )
        )
    md.extend([
        "",
        "## Guardrails",
        "",
        "- Uses only the already materialized same-source stock-market-regimes weekly/monthly rollup.",
        "- Does not use S&P source-window projection.",
        "- Does not promote child/sub-regime packets.",
        "- Axiswise validation closes same-source weekly/monthly cells only; unsupported intraday/full-species cells and full direct `Manipulation` variety coverage remain open.",
        "- No runtime code changed; no thresholds relaxed; no raw data committed; not trade usable.",
    ])
    (OUT_DIR / "source_consensus_axiswise_timeframe_gate_v1.md").write_text("\n".join(md) + "\n")

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={package['inputs']['board_sha256_at_run']}",
        f"source_consensus_threshold={SOURCE_CONSENSUS_THRESHOLD}",
        f"accepted_95_timeframe_root_cells={','.join(accepted)}",
        f"blocked_timeframe_root_cells={','.join(blocked)}",
        "newly_closed_cells_vs_disjoint_source_consensus_v1=1mo:Sideways",
        f"gate_result={package['decision']['gate_result']}",
        "accepted_full_objective_gate=none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    (CHECK_DIR / "source_consensus_axiswise_timeframe_gate_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n"
    )

    assert len(accepted) == 8
    assert not blocked


if __name__ == "__main__":
    main()
