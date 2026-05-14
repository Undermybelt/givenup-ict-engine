#!/usr/bin/env python3
"""Run a predeclared root-branch rescue recipe without touching runtime code.

The script reuses the clean RootTransitionTriad evaluator but replaces the
variant set and signal function before execution. This keeps the Board B
branch-path scoring/gates identical while testing a new, predeclared root
repair family for Bear, Sideways, and Crisis.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260511T195624+0800-codex-board-b-root-branch-rescue-predeclared-v1"
SCHEMA_VERSION = "board-b-root-branch-rescue-predeclared/v1"
RECIPE_ID = "RootBranchRescuePredeclaredV1"

RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
BASE_SCRIPT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T193803-codex-board-b-root-transition-triad-clean-v1/scripts/"
    "board_b_root_transition_triad_clean_v1.py"
)


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("root_transition_triad_clean_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import base evaluator: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def patch_module(module: Any) -> None:
    module.RUN_ID = RUN_ID
    module.SCHEMA_VERSION = SCHEMA_VERSION
    module.RECIPE_ID = RECIPE_ID
    module.RUN_ROOT = RUN_ROOT
    module.OUT_DIR = RUN_ROOT / "branch-rc-spa"
    module.CHECK_DIR = RUN_ROOT / "checks"
    module.FAIL_CLOSED_DIR = RUN_ROOT / "ict-engine-fail-closed"
    module.ALL_ROWS_CSV = module.OUT_DIR / "root_branch_rescue_variant_rows_v1.csv"
    module.SELECTED_ROWS_CSV = module.OUT_DIR / "root_branch_rescue_selected_rows_v1.csv"
    module.SUMMARY_CSV = module.OUT_DIR / "root_branch_rescue_branch_summary_v1.csv"
    module.PANEL_SUMMARY_CSV = module.OUT_DIR / "root_branch_rescue_panel_summary_v1.csv"
    module.REPORT_JSON = module.OUT_DIR / "root_branch_rescue_rc_spa_report_v1.json"
    module.REPORT_MD = module.OUT_DIR / "root_branch_rescue_rc_spa_report_v1.md"
    module.ASSERTIONS = module.CHECK_DIR / "root_branch_rescue_v1_assertions.out"
    module.FAIL_CLOSED_MD = module.FAIL_CLOSED_DIR / "root_branch_rescue_fail_closed_summary_v1.md"
    module.VARIANTS = [
        {
            "variant_id": "bull_trend_slow_anchor",
            "mode": "trend",
            "lookback": 20,
            "ema": 50,
            "z": 1.3,
            "hold": {"1h": 16, "4h": 8, "1d": 10},
        },
        {
            "variant_id": "bear_breakdown_short_strict",
            "mode": "tail_short",
            "lookback": 5,
            "ema": 20,
            "z": 1.2,
            "hold": {"1h": 8, "4h": 5, "1d": 5},
        },
        {
            "variant_id": "bear_relief_reversal_fast",
            "mode": "bear_reversal_long",
            "lookback": 3,
            "ema": 20,
            "z": 1.15,
            "hold": {"1h": 6, "4h": 4, "1d": 4},
        },
        {
            "variant_id": "sideways_breakout_follow",
            "mode": "range_breakout",
            "lookback": 10,
            "ema": 20,
            "z": 1.0,
            "hold": {"1h": 8, "4h": 5, "1d": 5},
        },
        {
            "variant_id": "sideways_reversion_control",
            "mode": "reversion",
            "lookback": 5,
            "ema": 20,
            "z": 0.9,
            "hold": {"1h": 6, "4h": 4, "1d": 4},
        },
        {
            "variant_id": "crisis_relief_long_confirmed",
            "mode": "crisis_relief_long",
            "lookback": 3,
            "ema": 20,
            "z": 1.3,
            "hold": {"1h": 6, "4h": 4, "1d": 4},
        },
        {
            "variant_id": "crisis_tail_short_strict",
            "mode": "tail_short",
            "lookback": 3,
            "ema": 20,
            "z": 1.0,
            "hold": {"1h": 8, "4h": 5, "1d": 5},
        },
        {
            "variant_id": "crisis_defensive_rotation",
            "mode": "defensive",
            "lookback": 10,
            "ema": 20,
            "z": 1.0,
            "hold": {"1h": 12, "4h": 6, "1d": 8},
        },
    ]
    original_signal_direction = module.signal_direction

    def signal_direction(row: pd.Series, variant: dict[str, Any]) -> int:
        root = str(row["parent_regime_root"])
        mode = str(variant["mode"])
        trend = float(row.get(f"ret{int(variant['lookback'])}", row["ret5"]))
        z_value = float(row["z20"])
        close = float(row["close"])
        ema_value = float(row[f"ema{int(variant['ema'])}"])
        vix = float(row["source_ticker_vix"])
        atr_pct = float(row["atr_pct"])
        z_threshold = float(variant["z"])

        if root == "Bear" and mode == "bear_reversal_long":
            oversold = z_value <= -z_threshold or float(row["ret3"]) <= -max(0.006, atr_pct)
            confirmation = float(row["ret1"]) > 0 or close > float(row["ema20"])
            return 1 if oversold and confirmation and vix < 45 else 0

        if root == "Sideways" and mode == "range_breakout":
            low_slope = abs(float(row["ema20_slope"])) < max(0.006, atr_pct * 0.45)
            if not low_slope:
                return 0
            if z_value >= z_threshold:
                return 1
            if z_value <= -z_threshold:
                return -1
            return 0

        if root == "Crisis" and mode == "crisis_relief_long":
            panic = z_value <= -z_threshold or float(row["ret3"]) <= -max(0.010, atr_pct * 1.5)
            confirmation = float(row["ret1"]) > 0 and close > float(row["low20_prev"])
            return 1 if panic and confirmation and vix < 55 else 0

        return original_signal_direction(row, variant)

    module.signal_direction = signal_direction


def main() -> int:
    module = load_base_module()
    patch_module(module)
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
