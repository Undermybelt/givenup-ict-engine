#!/usr/bin/env python3
"""Run-local NQ intraday root-branch stress scorer for Board B.

This imports the existing Board B RC-SPA evaluator and swaps in a predeclared
NQ-only 5m/15m/1h variant set. It does not modify ict-engine runtime code or
the Auto-Quant checkout.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260511T201148+0800-codex-board-b-nq-intraday-root-branch-stress-v1"
SCHEMA_VERSION = "board-b-nq-intraday-root-branch-stress/v1"
RECIPE_ID = "NQIntradayRootBranchStressV1"

RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
BASE_SCRIPT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T193803-codex-board-b-root-transition-triad-clean-v1/scripts/"
    "board_b_root_transition_triad_clean_v1.py"
)
DATA_DIR = Path("/Users/thrill3r/Auto-Quant/user_data/data")


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
    module.ALL_ROWS_CSV = module.OUT_DIR / "nq_intraday_root_branch_stress_variant_rows_v1.csv"
    module.SELECTED_ROWS_CSV = module.OUT_DIR / "nq_intraday_root_branch_stress_selected_rows_v1.csv"
    module.SUMMARY_CSV = module.OUT_DIR / "nq_intraday_root_branch_stress_branch_summary_v1.csv"
    module.PANEL_SUMMARY_CSV = module.OUT_DIR / "nq_intraday_root_branch_stress_panel_summary_v1.csv"
    module.REPORT_JSON = module.OUT_DIR / "nq_intraday_root_branch_stress_rc_spa_report_v1.json"
    module.REPORT_MD = module.OUT_DIR / "nq_intraday_root_branch_stress_rc_spa_report_v1.md"
    module.ASSERTIONS = module.CHECK_DIR / "nq_intraday_root_branch_stress_v1_assertions.out"
    module.FAIL_CLOSED_MD = module.FAIL_CLOSED_DIR / "nq_intraday_root_branch_stress_fail_closed_summary_v1.md"
    module.PANELS = [
        ("NQ/USD", "15m", DATA_DIR / "NQ_USD-15m.feather"),
        ("NQ/USD", "1h", DATA_DIR / "NQ_USD-1h.feather"),
    ]
    module.VARIANTS = [
        {
            "variant_id": "bear_intraday_breakdown_short",
            "mode": "bear_breakdown_short",
            "lookback": 10,
            "ema": 20,
            "z": 0.9,
            "hold": {"15m": 12, "1h": 8},
        },
        {
            "variant_id": "bear_intraday_relief_long",
            "mode": "bear_relief_long",
            "lookback": 5,
            "ema": 20,
            "z": 1.15,
            "hold": {"15m": 8, "1h": 6},
        },
        {
            "variant_id": "bear_intraday_vol_compression_short",
            "mode": "bear_vol_compression_short",
            "lookback": 20,
            "ema": 50,
            "z": 0.7,
            "hold": {"15m": 16, "1h": 10},
        },
        {
            "variant_id": "sideways_intraday_band_reversion",
            "mode": "sideways_band_reversion",
            "lookback": 5,
            "ema": 20,
            "z": 0.85,
            "hold": {"15m": 8, "1h": 6},
        },
        {
            "variant_id": "sideways_intraday_range_breakout",
            "mode": "sideways_range_breakout",
            "lookback": 10,
            "ema": 20,
            "z": 1.05,
            "hold": {"15m": 10, "1h": 8},
        },
        {
            "variant_id": "sideways_intraday_microtrend_filter",
            "mode": "sideways_microtrend_filter",
            "lookback": 20,
            "ema": 50,
            "z": 0.65,
            "hold": {"15m": 10, "1h": 8},
        },
        {
            "variant_id": "crisis_intraday_tail_short",
            "mode": "crisis_tail_short",
            "lookback": 3,
            "ema": 20,
            "z": 0.9,
            "hold": {"15m": 12, "1h": 8},
        },
        {
            "variant_id": "crisis_intraday_relief_long",
            "mode": "crisis_relief_long",
            "lookback": 3,
            "ema": 20,
            "z": 1.25,
            "hold": {"15m": 8, "1h": 6},
        },
        {
            "variant_id": "crisis_intraday_abstain_defensive",
            "mode": "crisis_abstain_defensive",
            "lookback": 10,
            "ema": 50,
            "z": 0.8,
            "hold": {"15m": 8, "1h": 6},
        },
    ]

    original_signal_direction = module.signal_direction

    def signal_direction(row: pd.Series, variant: dict[str, Any]) -> int:
        root = str(row["parent_regime_root"])
        mode = str(variant["mode"])
        lookback = int(variant["lookback"])
        ema_col = f"ema{int(variant['ema'])}"
        trend = float(row.get(f"ret{lookback}", row["ret5"]))
        ret1 = float(row["ret1"])
        ret3 = float(row["ret3"])
        z_value = float(row["z20"])
        close = float(row["close"])
        ema_value = float(row[ema_col])
        ema20_slope = float(row["ema20_slope"])
        atr_pct = max(float(row["atr_pct"]), 1e-9)
        vix = float(row["source_ticker_vix"])
        z_threshold = float(variant["z"])
        low_slope = abs(ema20_slope) < max(0.0025, atr_pct * 0.35)

        if root == "Bear":
            if mode == "bear_breakdown_short":
                return -1 if trend < -max(0.0015, atr_pct * 0.30) and close < ema_value else 0
            if mode == "bear_relief_long":
                oversold = z_value <= -z_threshold or ret3 <= -max(0.003, atr_pct)
                confirmation = ret1 > 0 and close > float(row["low20_prev"])
                return 1 if oversold and confirmation and vix < 45 else 0
            if mode == "bear_vol_compression_short":
                compression = low_slope and abs(z_value) < max(1.0, z_threshold + 0.25)
                return -1 if compression and ret1 < 0 and close < float(row["ema20"]) else 0

        if root == "Sideways":
            if mode == "sideways_band_reversion":
                if z_value >= z_threshold and low_slope:
                    return -1
                if z_value <= -z_threshold and low_slope:
                    return 1
                return 0
            if mode == "sideways_range_breakout":
                if not low_slope:
                    return 0
                if close > float(row["high20_prev"]) and ret1 > 0:
                    return 1
                if close < float(row["low20_prev"]) and ret1 < 0:
                    return -1
                return 0
            if mode == "sideways_microtrend_filter":
                if not low_slope:
                    return 0
                return 1 if trend > max(0.001, atr_pct * 0.20) else (-1 if trend < -max(0.001, atr_pct * 0.20) else 0)

        if root == "Crisis":
            if mode == "crisis_tail_short":
                return -1 if (trend < 0 or ret3 < -max(0.004, atr_pct)) and (close < ema_value or vix >= 28) else 0
            if mode == "crisis_relief_long":
                panic = z_value <= -z_threshold or ret3 <= -max(0.006, atr_pct * 1.25)
                return 1 if panic and ret1 > 0 and vix < 55 else 0
            if mode == "crisis_abstain_defensive":
                return -1 if ret1 < 0 and close < ema_value and vix >= 35 else 0

        return original_signal_direction(row, variant)

    module.signal_direction = signal_direction


def main() -> int:
    module = load_base_module()
    patch_module(module)
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
