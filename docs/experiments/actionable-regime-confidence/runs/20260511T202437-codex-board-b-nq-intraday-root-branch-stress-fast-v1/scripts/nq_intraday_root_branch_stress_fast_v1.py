#!/usr/bin/env python3
"""Fast run-local NQ intraday root-branch stress scorer for Board B.

This is a single-writer retry of the 201148 slice. It imports the existing
Board B RC-SPA evaluator, keeps the same root-first branch contract, and
overrides only the run-local panel/variant definitions plus a vectorized trade
row builder so the 5m NQ panel can finish inside the loop.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260511T202437+0800-codex-board-b-nq-intraday-root-branch-stress-fast-v1"
SCHEMA_VERSION = "board-b-nq-intraday-root-branch-stress-fast/v1"
RECIPE_ID = "NQIntradayRootBranchStressFastV1"

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


def _arr(df: pd.DataFrame, column: str) -> np.ndarray:
    return df[column].to_numpy(dtype=float)


def _safe_col(df: pd.DataFrame, column: str, fallback: str) -> np.ndarray:
    return df[column].to_numpy(dtype=float) if column in df else df[fallback].to_numpy(dtype=float)


def _select_non_overlapping(candidates: np.ndarray, hold: int, size: int) -> list[int]:
    selected: list[int] = []
    next_allowed = 0
    for raw_idx in candidates.tolist():
        idx = int(raw_idx)
        if idx < next_allowed or idx + hold >= size:
            continue
        selected.append(idx)
        next_allowed = idx + hold + 1
    return selected


def _signal_vector(df: pd.DataFrame, variant: dict[str, Any]) -> np.ndarray:
    roots = df["parent_regime_root"].astype(str).to_numpy()
    mode = str(variant["mode"])
    lookback = int(variant["lookback"])
    ema_col = f"ema{int(variant['ema'])}"
    trend = _safe_col(df, f"ret{lookback}", "ret5")
    ret1 = _arr(df, "ret1")
    ret3 = _arr(df, "ret3")
    z20 = _arr(df, "z20")
    close = _arr(df, "close")
    ema_value = _arr(df, ema_col)
    ema20 = _arr(df, "ema20")
    ema20_slope = _arr(df, "ema20_slope")
    atr_pct = np.maximum(_arr(df, "atr_pct"), 1e-9)
    vix = _arr(df, "source_ticker_vix")
    high20_prev = _arr(df, "high20_prev")
    low20_prev = _arr(df, "low20_prev")
    z_threshold = float(variant["z"])
    low_slope = np.abs(ema20_slope) < np.maximum(0.0025, atr_pct * 0.35)
    signal = np.zeros(len(df), dtype=np.int8)

    bull = roots == "Bull"
    signal[bull & (trend > 0) & (close > ema_value)] = 1

    bear = roots == "Bear"
    if mode == "bear_breakdown_short":
        mask = bear & (trend < -np.maximum(0.0015, atr_pct * 0.30)) & (close < ema_value)
        signal[mask] = -1
    elif mode == "bear_relief_long":
        oversold = (z20 <= -z_threshold) | (ret3 <= -np.maximum(0.003, atr_pct))
        confirmation = (ret1 > 0) & (close > low20_prev)
        signal[bear & oversold & confirmation & (vix < 45)] = 1
    elif mode == "bear_vol_compression_short":
        compression = low_slope & (np.abs(z20) < max(1.0, z_threshold + 0.25))
        signal[bear & compression & (ret1 < 0) & (close < ema20)] = -1

    sideways = roots == "Sideways"
    if mode == "sideways_band_reversion":
        signal[sideways & low_slope & (z20 >= z_threshold)] = -1
        signal[sideways & low_slope & (z20 <= -z_threshold)] = 1
    elif mode == "sideways_range_breakout":
        signal[sideways & low_slope & (close > high20_prev) & (ret1 > 0)] = 1
        signal[sideways & low_slope & (close < low20_prev) & (ret1 < 0)] = -1
    elif mode == "sideways_microtrend_filter":
        threshold = np.maximum(0.001, atr_pct * 0.20)
        signal[sideways & low_slope & (trend > threshold)] = 1
        signal[sideways & low_slope & (trend < -threshold)] = -1

    crisis = roots == "Crisis"
    if mode == "crisis_tail_short":
        mask = (
            crisis
            & ((trend < 0) | (ret3 < -np.maximum(0.004, atr_pct)))
            & ((close < ema_value) | (vix >= 28))
        )
        signal[mask] = -1
    elif mode == "crisis_relief_long":
        panic = (z20 <= -z_threshold) | (ret3 <= -np.maximum(0.006, atr_pct * 1.25))
        signal[crisis & panic & (ret1 > 0) & (vix < 55)] = 1
    elif mode == "crisis_abstain_defensive":
        signal[crisis & (ret1 < 0) & (close < ema_value) & (vix >= 35)] = -1

    return signal


def _fast_build_trade_rows(module: Any, df: pd.DataFrame, variant: dict[str, Any]) -> list[dict[str, Any]]:
    if df.empty:
        return []
    variant_id = str(variant["variant_id"])
    timeframe = str(df["timeframe"].iloc[0])
    market = str(df["market"].iloc[0])
    hold = int(variant["hold"].get(timeframe, 5))
    cost = float(module.roundtrip_cost(market, timeframe))
    signal = _signal_vector(df, variant)
    candidates = np.flatnonzero(signal != 0)
    selected = _select_non_overlapping(candidates, hold, len(df))
    if not selected:
        return []

    idx = np.array(selected, dtype=int)
    exit_idx = idx + hold
    close = _arr(df, "close")
    entry = close[idx]
    exit_price = close[exit_idx]
    valid = (entry > 0) & (exit_price > 0)
    if not np.all(valid):
        idx = idx[valid]
        exit_idx = exit_idx[valid]
        entry = entry[valid]
        exit_price = exit_price[valid]
    if len(idx) == 0:
        return []

    direction = signal[idx].astype(int)
    gross = direction * (exit_price / entry - 1.0)
    pnl = gross - cost
    rows: list[dict[str, Any]] = []
    roots = df["parent_regime_root"].astype(str).to_numpy()
    dates = df["date"].to_numpy()
    session_dates = df["session_date"].to_numpy()
    floors = _arr(df, "parent_regime_confidence_floor")
    conf = _arr(df, "source_ticker_confidence")
    vix = _arr(df, "source_ticker_vix")
    lookup_status = df["root_lookup_status"].astype(str).to_numpy()

    for pos, open_idx in enumerate(idx.tolist()):
        root = str(roots[open_idx])
        if root not in module.ROOTS:
            continue
        fields = module.branch_fields(root)
        close_idx = int(exit_idx[pos])
        open_ts = pd.Timestamp(dates[open_idx])
        close_ts = pd.Timestamp(dates[close_idx])
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "run_id": RUN_ID,
                "recipe_id": RECIPE_ID,
                "variant_id": variant_id,
                "market": market,
                "timeframe": timeframe,
                "trade_id": f"{RECIPE_ID}:{variant_id}:{market}:{timeframe}:{open_idx}",
                "open_date": open_ts.isoformat(),
                "close_date": close_ts.isoformat(),
                "open_session_date": pd.Timestamp(session_dates[open_idx]).date().isoformat(),
                "source_anchor": module.SOURCE_TICKER,
                "parent_regime_root": root,
                "parent_regime_confidence_floor": float(floors[open_idx]),
                "source_ticker_confidence": float(conf[open_idx]),
                "source_ticker_vix": float(vix[open_idx]),
                "manipulation_overlay_state": "not_consumed_no_direct_event_rows",
                "sub_regime_tags": fields["sub_regime_tags"],
                "sub_sub_regime_or_profit_factor": fields["sub_sub_regime_or_profit_factor"],
                "profit_factor_family": fields["profit_factor_family"],
                "profit_factor_leaf": f"{RECIPE_ID}:{variant_id}",
                "regime_profit_branch_path": module.branch_path(root, variant_id),
                "regime_profit_branch_path_version": SCHEMA_VERSION,
                "trade_or_bar_horizon": f"{timeframe}_hold_{hold}",
                "allowed_action": fields["allowed_action"],
                "suppression_rule": fields["suppression_rule"],
                "direction": "long" if int(direction[pos]) > 0 else "short",
                "direction_sign": int(direction[pos]),
                "entry_close": float(entry[pos]),
                "exit_close": float(exit_price[pos]),
                "gross_return": float(gross[pos]),
                "roundtrip_cost": cost,
                "profit_ratio_net": float(pnl[pos]),
                "year_fold": int(open_ts.year),
                "root_lookup_status": str(lookup_status[open_idx]),
            }
        )
    return rows


def patch_module(module: Any) -> None:
    module.RUN_ID = RUN_ID
    module.SCHEMA_VERSION = SCHEMA_VERSION
    module.RECIPE_ID = RECIPE_ID
    module.RUN_ROOT = RUN_ROOT
    module.OUT_DIR = RUN_ROOT / "branch-rc-spa"
    module.CHECK_DIR = RUN_ROOT / "checks"
    module.FAIL_CLOSED_DIR = RUN_ROOT / "ict-engine-fail-closed"
    module.ALL_ROWS_CSV = module.OUT_DIR / "nq_intraday_root_branch_stress_fast_variant_rows_v1.csv"
    module.SELECTED_ROWS_CSV = module.OUT_DIR / "nq_intraday_root_branch_stress_fast_selected_rows_v1.csv"
    module.SUMMARY_CSV = module.OUT_DIR / "nq_intraday_root_branch_stress_fast_branch_summary_v1.csv"
    module.PANEL_SUMMARY_CSV = module.OUT_DIR / "nq_intraday_root_branch_stress_fast_panel_summary_v1.csv"
    module.REPORT_JSON = module.OUT_DIR / "nq_intraday_root_branch_stress_fast_rc_spa_report_v1.json"
    module.REPORT_MD = module.OUT_DIR / "nq_intraday_root_branch_stress_fast_rc_spa_report_v1.md"
    module.ASSERTIONS = module.CHECK_DIR / "nq_intraday_root_branch_stress_fast_v1_assertions.out"
    module.FAIL_CLOSED_MD = module.FAIL_CLOSED_DIR / "nq_intraday_root_branch_stress_fast_fail_closed_summary_v1.md"
    module.PANELS = [
        ("NQ/USD", "5m", DATA_DIR / "NQ_USD-5m.feather"),
        ("NQ/USD", "15m", DATA_DIR / "NQ_USD-15m.feather"),
        ("NQ/USD", "1h", DATA_DIR / "NQ_USD-1h.feather"),
    ]
    module.VARIANTS = [
        {"variant_id": "bear_intraday_breakdown_short", "mode": "bear_breakdown_short", "lookback": 10, "ema": 20, "z": 0.9, "hold": {"5m": 18, "15m": 12, "1h": 8}},
        {"variant_id": "bear_intraday_relief_long", "mode": "bear_relief_long", "lookback": 5, "ema": 20, "z": 1.15, "hold": {"5m": 12, "15m": 8, "1h": 6}},
        {"variant_id": "bear_intraday_vol_compression_short", "mode": "bear_vol_compression_short", "lookback": 20, "ema": 50, "z": 0.7, "hold": {"5m": 24, "15m": 16, "1h": 10}},
        {"variant_id": "sideways_intraday_band_reversion", "mode": "sideways_band_reversion", "lookback": 5, "ema": 20, "z": 0.85, "hold": {"5m": 10, "15m": 8, "1h": 6}},
        {"variant_id": "sideways_intraday_range_breakout", "mode": "sideways_range_breakout", "lookback": 10, "ema": 20, "z": 1.05, "hold": {"5m": 14, "15m": 10, "1h": 8}},
        {"variant_id": "sideways_intraday_microtrend_filter", "mode": "sideways_microtrend_filter", "lookback": 20, "ema": 50, "z": 0.65, "hold": {"5m": 16, "15m": 10, "1h": 8}},
        {"variant_id": "crisis_intraday_tail_short", "mode": "crisis_tail_short", "lookback": 3, "ema": 20, "z": 0.9, "hold": {"5m": 18, "15m": 12, "1h": 8}},
        {"variant_id": "crisis_intraday_relief_long", "mode": "crisis_relief_long", "lookback": 3, "ema": 20, "z": 1.25, "hold": {"5m": 10, "15m": 8, "1h": 6}},
        {"variant_id": "crisis_intraday_abstain_defensive", "mode": "crisis_abstain_defensive", "lookback": 10, "ema": 50, "z": 0.8, "hold": {"5m": 12, "15m": 8, "1h": 6}},
    ]

    def build_trade_rows(df: pd.DataFrame, variant: dict[str, Any]) -> list[dict[str, Any]]:
        return _fast_build_trade_rows(module, df, variant)

    module.build_trade_rows = build_trade_rows


def main() -> int:
    module = load_base_module()
    patch_module(module)
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
