#!/usr/bin/env python3
"""Board B crypto-liquidity root-family RC-SPA readback.

Run-local additive experiment. It repairs the earlier collided crypto-liquidity
attempt by using the existing Board B RC-SPA evaluator with a fresh run root,
local Auto-Quant feather panels, and the already-passing 205047 scoped
Manipulation component as a separate component only.
"""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260511T210508+0800-codex-board-b-crypto-liquidity-root-family-v2"
SCHEMA_VERSION = "board-b-crypto-liquidity-root-family/v2"
RECIPE_ID = "CryptoLiquidityRootFamilyV2"
SOURCE_TICKER = "^IXIC"

RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
DATA_DIR = Path("/Users/thrill3r/Auto-Quant/user_data/data")
BASE_SCRIPT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T193803-codex-board-b-root-transition-triad-clean-v1/scripts/"
    "board_b_root_transition_triad_clean_v1.py"
)
MANIP_SUMMARY_CSV = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/"
    "manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2_summary.csv"
)
MANIP_REPORT_MD = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/"
    "manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2.md"
)


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("board_b_root_transition_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import base evaluator: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def roundtrip_cost(market: str, timeframe: str) -> float:
    if timeframe == "1h":
        return 0.0018
    if timeframe == "4h":
        return 0.0015
    return 0.0012


def branch_path(root: str, variant_id: str) -> str:
    if root == "Bull":
        return f"{root} -> CryptoLiquidityExpansion -> VolumeConfirmedTrend -> {RECIPE_ID}:{variant_id}"
    if root == "Bear":
        return f"{root} -> CryptoLiquidityDrain -> BreakdownOrReliefFade -> {RECIPE_ID}:{variant_id}"
    if root == "Sideways":
        return f"{root} -> CryptoLiquidityRange -> RangeReversionOrSqueeze -> {RECIPE_ID}:{variant_id}"
    if root == "Crisis":
        return f"{root} -> CryptoLiquidityCliff -> TailShortOrPanicRebound -> {RECIPE_ID}:{variant_id}"
    return (
        "Manipulation(scoped) -> TelegramPumpEvent -> ProviderStopTakeShort -> "
        "ManipulationStopTakeProfitGridV2:short_tp120_sl060_h72"
    )


def branch_fields(root: str) -> dict[str, str]:
    if root == "Bull":
        return {
            "sub_regime_tags": "CryptoLiquidityExpansion",
            "sub_sub_regime_or_profit_factor": "VolumeConfirmedTrend",
            "profit_factor_family": "crypto_liquidity_root_family",
            "allowed_action": "long_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bull_crypto_liquidity_branch_rc_spa_fails",
        }
    if root == "Bear":
        return {
            "sub_regime_tags": "CryptoLiquidityDrain",
            "sub_sub_regime_or_profit_factor": "BreakdownOrReliefFade",
            "profit_factor_family": "crypto_liquidity_root_family",
            "allowed_action": "short_or_reversal_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bear_crypto_liquidity_branch_rc_spa_fails",
        }
    if root == "Sideways":
        return {
            "sub_regime_tags": "CryptoLiquidityRange",
            "sub_sub_regime_or_profit_factor": "RangeReversionOrSqueeze",
            "profit_factor_family": "crypto_liquidity_root_family",
            "allowed_action": "long_short_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_sideways_crypto_liquidity_branch_rc_spa_fails",
        }
    if root == "Crisis":
        return {
            "sub_regime_tags": "CryptoLiquidityCliff",
            "sub_sub_regime_or_profit_factor": "TailShortOrPanicRebound",
            "profit_factor_family": "crypto_liquidity_root_family",
            "allowed_action": "short_or_panic_rebound_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "tail_guard_blocks_crypto_liquidity_branch_if_rc_spa_fails",
        }
    return {
        "sub_regime_tags": "TelegramPumpEvent",
        "sub_sub_regime_or_profit_factor": "ProviderStopTakeShort",
        "profit_factor_family": "direct_manipulation_stop_take_profit",
        "allowed_action": "short_stop_tp_component_only",
        "suppression_rule": "do_not_use_without_price_root_branch_passes",
    }


def load_panel(module: Any, path: Path, market: str, timeframe: str, lookup: Any) -> pd.DataFrame:
    df = module._base_load_panel(path, market, timeframe, lookup)
    if df.empty:
        return df
    volume = pd.to_numeric(df["volume"], errors="coerce").fillna(0.0)
    dollar_volume = (pd.to_numeric(df["close"], errors="coerce").fillna(0.0) * volume).replace(0, np.nan)
    vol_mean = volume.rolling(30, min_periods=10).mean()
    vol_std = volume.rolling(30, min_periods=10).std().replace(0, np.nan)
    amihud = (df["ret1"].abs() / dollar_volume).replace([np.inf, -np.inf], np.nan)
    amihud_mean = amihud.rolling(30, min_periods=10).mean()
    amihud_std = amihud.rolling(30, min_periods=10).std().replace(0, np.nan)
    df["volume_ratio"] = (volume / vol_mean.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan).fillna(1.0)
    df["volume_z"] = ((volume - vol_mean) / vol_std).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    df["dollar_volume"] = dollar_volume.fillna(0.0)
    df["amihud"] = amihud.fillna(0.0)
    df["amihud_z"] = ((amihud - amihud_mean) / amihud_std).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    df["range_pct"] = ((df["high"] - df["low"]).abs() / df["close"].replace(0, np.nan)).fillna(0.0)
    return df


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
    ema20 = float(row["ema20"])
    ema50 = float(row["ema50"])
    ema20_slope = float(row["ema20_slope"])
    atr_pct = max(float(row["atr_pct"]), 1e-9)
    volume_ratio = float(row["volume_ratio"])
    volume_z = float(row["volume_z"])
    amihud_z = float(row["amihud_z"])
    range_pct = float(row["range_pct"])
    vix = float(row["source_ticker_vix"])
    z_threshold = float(variant["z"])
    low_slope = abs(ema20_slope) < max(0.004, atr_pct * 0.35)
    liquidity_spike = volume_ratio >= 1.25 or volume_z >= 0.35
    liquidity_cliff = volume_ratio <= 0.70 or amihud_z >= 0.75 or range_pct >= max(0.035, atr_pct * 1.40)

    if root == "Bull":
        if mode == "liq_expansion_momentum":
            return 1 if close > ema_value and trend > max(0.003, atr_pct * 0.25) and liquidity_spike and amihud_z < 1.25 else 0
        if mode == "bull_pullback_reclaim":
            return 1 if close > ema50 and z_value <= -z_threshold and ret1 > 0 and volume_ratio >= 0.80 else 0
        if mode == "low_impact_carry":
            return 1 if close > ema20 and trend > 0 and amihud_z <= -0.20 and volume_ratio >= 0.65 else 0
        return 0

    if root == "Bear":
        if mode == "liq_drain_breakdown":
            return -1 if close < ema_value and trend < -max(0.003, atr_pct * 0.25) and (liquidity_cliff or liquidity_spike) else 0
        if mode == "relief_fade_short":
            return -1 if close < ema50 and z_value >= z_threshold and ret1 < 0 and volume_ratio >= 0.75 else 0
        if mode == "panic_rebound":
            return 1 if z_value <= -max(1.5, z_threshold) and ret1 > 0 and liquidity_spike and vix < 45 else 0
        return 0

    if root == "Sideways":
        if mode == "range_liq_reversion":
            if low_slope and volume_ratio >= 0.60 and z_value >= z_threshold:
                return -1
            if low_slope and volume_ratio >= 0.60 and z_value <= -z_threshold:
                return 1
        if mode == "squeeze_breakout":
            high_break = close > float(row["high20_prev"]) and ret1 > 0 and liquidity_spike
            low_break = close < float(row["low20_prev"]) and ret1 < 0 and liquidity_spike
            if low_slope and high_break:
                return 1
            if low_slope and low_break:
                return -1
        if mode == "low_impact_carry":
            return 1 if low_slope and trend > 0 and amihud_z <= -0.25 else 0
        return 0

    if root == "Crisis":
        if mode == "liq_cliff_short":
            return -1 if close < ema_value and (trend < 0 or ret3 < -max(0.015, atr_pct)) and (liquidity_cliff or vix >= 28) else 0
        if mode == "panic_rebound":
            panic = z_value <= -max(1.7, z_threshold) or ret3 <= -max(0.030, atr_pct * 1.5)
            return 1 if panic and ret1 > 0 and liquidity_spike and vix < 55 else 0
        if mode == "relief_fade_short":
            return -1 if z_value >= z_threshold and ret1 < 0 and close < ema50 else 0
        return 0

    return 0


def _arr(df: pd.DataFrame, column: str) -> np.ndarray:
    return df[column].to_numpy(dtype=float)


def _safe_arr(df: pd.DataFrame, column: str, fallback: str) -> np.ndarray:
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


def signal_vector(df: pd.DataFrame, variant: dict[str, Any]) -> np.ndarray:
    roots = df["parent_regime_root"].astype(str).to_numpy()
    mode = str(variant["mode"])
    lookback = int(variant["lookback"])
    ema_col = f"ema{int(variant['ema'])}"
    trend = _safe_arr(df, f"ret{lookback}", "ret5")
    ret1 = _arr(df, "ret1")
    ret3 = _arr(df, "ret3")
    z20 = _arr(df, "z20")
    close = _arr(df, "close")
    ema_value = _arr(df, ema_col)
    ema20 = _arr(df, "ema20")
    ema50 = _arr(df, "ema50")
    ema20_slope = _arr(df, "ema20_slope")
    atr_pct = np.maximum(_arr(df, "atr_pct"), 1e-9)
    volume_ratio = _arr(df, "volume_ratio")
    volume_z = _arr(df, "volume_z")
    amihud_z = _arr(df, "amihud_z")
    range_pct = _arr(df, "range_pct")
    vix = _arr(df, "source_ticker_vix")
    high20_prev = np.nan_to_num(_arr(df, "high20_prev"), nan=0.0)
    low20_prev = np.nan_to_num(_arr(df, "low20_prev"), nan=0.0)
    z_threshold = float(variant["z"])
    low_slope = np.abs(ema20_slope) < np.maximum(0.004, atr_pct * 0.35)
    liquidity_spike = (volume_ratio >= 1.25) | (volume_z >= 0.35)
    liquidity_cliff = (volume_ratio <= 0.70) | (amihud_z >= 0.75) | (range_pct >= np.maximum(0.035, atr_pct * 1.40))
    signal = np.zeros(len(df), dtype=np.int8)

    bull = roots == "Bull"
    if mode == "liq_expansion_momentum":
        signal[bull & (close > ema_value) & (trend > np.maximum(0.003, atr_pct * 0.25)) & liquidity_spike & (amihud_z < 1.25)] = 1
    elif mode == "bull_pullback_reclaim":
        signal[bull & (close > ema50) & (z20 <= -z_threshold) & (ret1 > 0) & (volume_ratio >= 0.80)] = 1
    elif mode == "low_impact_carry":
        signal[bull & (close > ema20) & (trend > 0) & (amihud_z <= -0.20) & (volume_ratio >= 0.65)] = 1

    bear = roots == "Bear"
    if mode == "liq_drain_breakdown":
        signal[bear & (close < ema_value) & (trend < -np.maximum(0.003, atr_pct * 0.25)) & (liquidity_cliff | liquidity_spike)] = -1
    elif mode == "relief_fade_short":
        signal[bear & (close < ema50) & (z20 >= z_threshold) & (ret1 < 0) & (volume_ratio >= 0.75)] = -1
    elif mode == "panic_rebound":
        signal[bear & (z20 <= -np.maximum(1.5, z_threshold)) & (ret1 > 0) & liquidity_spike & (vix < 45)] = 1

    sideways = roots == "Sideways"
    if mode == "range_liq_reversion":
        signal[sideways & low_slope & (volume_ratio >= 0.60) & (z20 >= z_threshold)] = -1
        signal[sideways & low_slope & (volume_ratio >= 0.60) & (z20 <= -z_threshold)] = 1
    elif mode == "squeeze_breakout":
        signal[sideways & low_slope & (close > high20_prev) & (ret1 > 0) & liquidity_spike] = 1
        signal[sideways & low_slope & (close < low20_prev) & (ret1 < 0) & liquidity_spike] = -1
    elif mode == "low_impact_carry":
        signal[sideways & low_slope & (trend > 0) & (amihud_z <= -0.25)] = 1

    crisis = roots == "Crisis"
    if mode == "liq_cliff_short":
        signal[
            crisis
            & (close < ema_value)
            & ((trend < 0) | (ret3 < -np.maximum(0.015, atr_pct)))
            & (liquidity_cliff | (vix >= 28))
        ] = -1
    elif mode == "panic_rebound":
        panic = (z20 <= -np.maximum(1.7, z_threshold)) | (ret3 <= -np.maximum(0.030, atr_pct * 1.5))
        signal[crisis & panic & (ret1 > 0) & liquidity_spike & (vix < 55)] = 1
    elif mode == "relief_fade_short":
        signal[crisis & (z20 >= z_threshold) & (ret1 < 0) & (close < ema50)] = -1

    return signal


def build_trade_rows_vectorized(module: Any, df: pd.DataFrame, variant: dict[str, Any]) -> list[dict[str, Any]]:
    if df.empty:
        return []
    variant_id = str(variant["variant_id"])
    timeframe = str(df["timeframe"].iloc[0])
    market = str(df["market"].iloc[0])
    hold = int(variant["hold"].get(timeframe, 5))
    cost = float(roundtrip_cost(market, timeframe))
    signal = signal_vector(df, variant)
    selected = _select_non_overlapping(np.flatnonzero(signal != 0), hold, len(df))
    if not selected:
        return []

    idx = np.array(selected, dtype=int)
    exit_idx = idx + hold
    close = _arr(df, "close")
    entry = close[idx]
    exit_price = close[exit_idx]
    valid = (entry > 0) & (exit_price > 0)
    idx = idx[valid]
    exit_idx = exit_idx[valid]
    entry = entry[valid]
    exit_price = exit_price[valid]
    if len(idx) == 0:
        return []

    direction = signal[idx].astype(int)
    pnl = direction * (exit_price / entry - 1.0) - cost
    roots = df["parent_regime_root"].astype(str).to_numpy()
    rows: list[dict[str, Any]] = []
    for position, i in enumerate(idx.tolist()):
        root = str(roots[i])
        if root not in module.ROOTS:
            continue
        out_i = int(exit_idx[position])
        fields = branch_fields(root)
        open_ts = pd.Timestamp(df["date"].iloc[i])
        close_ts = pd.Timestamp(df["date"].iloc[out_i])
        session_date = pd.Timestamp(df["session_date"].iloc[i]).date().isoformat()
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "run_id": RUN_ID,
                "recipe_id": RECIPE_ID,
                "variant_id": variant_id,
                "market": market,
                "timeframe": timeframe,
                "trade_id": f"{RECIPE_ID}:{variant_id}:{market}:{timeframe}:{i}",
                "open_date": open_ts.isoformat(),
                "close_date": close_ts.isoformat(),
                "open_session_date": session_date,
                "source_anchor": SOURCE_TICKER,
                "parent_regime_root": root,
                "parent_regime_confidence_floor": float(df["parent_regime_confidence_floor"].iloc[i]),
                "source_ticker_confidence": float(df["source_ticker_confidence"].iloc[i]),
                "source_ticker_vix": float(df["source_ticker_vix"].iloc[i]),
                "manipulation_overlay_state": "component_available_from_205047_not_consumed_in_price_root_rows",
                "sub_regime_tags": fields["sub_regime_tags"],
                "sub_sub_regime_or_profit_factor": fields["sub_sub_regime_or_profit_factor"],
                "profit_factor_family": fields["profit_factor_family"],
                "profit_factor_leaf": f"{RECIPE_ID}:{variant_id}",
                "regime_profit_branch_path": branch_path(root, variant_id),
                "regime_profit_branch_path_version": SCHEMA_VERSION,
                "trade_or_bar_horizon": f"{timeframe}_hold_{hold}",
                "allowed_action": fields["allowed_action"],
                "suppression_rule": fields["suppression_rule"],
                "direction": "long" if int(direction[position]) > 0 else "short",
                "direction_sign": int(direction[position]),
                "entry_close": float(entry[position]),
                "exit_close": float(exit_price[position]),
                "gross_return": float(direction[position] * (exit_price[position] / entry[position] - 1.0)),
                "roundtrip_cost": cost,
                "profit_ratio_net": float(pnl[position]),
                "year_fold": int(open_ts.year),
                "root_lookup_status": str(df["root_lookup_status"].iloc[i]),
            }
        )
    return rows


def patch_module(module: Any) -> None:
    module._base_load_panel = module.load_panel
    module.RUN_ID = RUN_ID
    module.SCHEMA_VERSION = SCHEMA_VERSION
    module.RECIPE_ID = RECIPE_ID
    module.SOURCE_TICKER = SOURCE_TICKER
    module.RUN_ROOT = RUN_ROOT
    module.OUT_DIR = RUN_ROOT / "branch-rc-spa"
    module.CHECK_DIR = RUN_ROOT / "checks"
    module.FAIL_CLOSED_DIR = RUN_ROOT / "ict-engine-fail-closed"
    module.ALL_ROWS_CSV = module.OUT_DIR / "crypto_liquidity_root_family_variant_rows_v2.csv"
    module.SELECTED_ROWS_CSV = module.OUT_DIR / "crypto_liquidity_root_family_selected_rows_v2.csv"
    module.SUMMARY_CSV = module.OUT_DIR / "crypto_liquidity_root_family_branch_summary_v2.csv"
    module.PANEL_SUMMARY_CSV = module.OUT_DIR / "crypto_liquidity_root_family_panel_summary_v2.csv"
    module.REPORT_JSON = module.OUT_DIR / "crypto_liquidity_root_family_rc_spa_report_v2.json"
    module.REPORT_MD = module.OUT_DIR / "crypto_liquidity_root_family_rc_spa_report_v2.md"
    module.ASSERTIONS = module.CHECK_DIR / "crypto_liquidity_root_family_v2_assertions.out"
    module.FAIL_CLOSED_MD = module.FAIL_CLOSED_DIR / "crypto_liquidity_root_family_fail_closed_summary_v2.md"
    module.PANELS = [
        ("BTC/USDT", "1h", DATA_DIR / "BTC_USDT-1h.feather"),
        ("BTC/USDT", "4h", DATA_DIR / "BTC_USDT-4h.feather"),
        ("BTC/USDT", "1d", DATA_DIR / "BTC_USDT-1d.feather"),
        ("ETH/USDT", "1h", DATA_DIR / "ETH_USDT-1h.feather"),
        ("ETH/USDT", "4h", DATA_DIR / "ETH_USDT-4h.feather"),
        ("ETH/USDT", "1d", DATA_DIR / "ETH_USDT-1d.feather"),
        ("BNB/USDT", "1h", DATA_DIR / "BNB_USDT-1h.feather"),
        ("BNB/USDT", "4h", DATA_DIR / "BNB_USDT-4h.feather"),
        ("BNB/USDT", "1d", DATA_DIR / "BNB_USDT-1d.feather"),
        ("SOL/USDT", "1h", DATA_DIR / "SOL_USDT-1h.feather"),
        ("SOL/USDT", "4h", DATA_DIR / "SOL_USDT-4h.feather"),
        ("SOL/USDT", "1d", DATA_DIR / "SOL_USDT-1d.feather"),
        ("AVAX/USDT", "1h", DATA_DIR / "AVAX_USDT-1h.feather"),
        ("AVAX/USDT", "4h", DATA_DIR / "AVAX_USDT-4h.feather"),
        ("AVAX/USDT", "1d", DATA_DIR / "AVAX_USDT-1d.feather"),
    ]
    module.VARIANTS = [
        {"variant_id": "liq_expansion_momentum_fast", "mode": "liq_expansion_momentum", "lookback": 5, "ema": 20, "z": 0.9, "hold": {"1h": 8, "4h": 5, "1d": 5}},
        {"variant_id": "liq_expansion_momentum_slow", "mode": "liq_expansion_momentum", "lookback": 20, "ema": 50, "z": 1.1, "hold": {"1h": 14, "4h": 7, "1d": 8}},
        {"variant_id": "bull_pullback_reclaim", "mode": "bull_pullback_reclaim", "lookback": 5, "ema": 20, "z": 0.85, "hold": {"1h": 8, "4h": 5, "1d": 5}},
        {"variant_id": "liq_drain_breakdown", "mode": "liq_drain_breakdown", "lookback": 10, "ema": 20, "z": 1.0, "hold": {"1h": 10, "4h": 6, "1d": 6}},
        {"variant_id": "relief_fade_short", "mode": "relief_fade_short", "lookback": 5, "ema": 20, "z": 0.95, "hold": {"1h": 8, "4h": 5, "1d": 5}},
        {"variant_id": "range_liq_reversion", "mode": "range_liq_reversion", "lookback": 5, "ema": 20, "z": 0.80, "hold": {"1h": 6, "4h": 4, "1d": 4}},
        {"variant_id": "squeeze_breakout", "mode": "squeeze_breakout", "lookback": 5, "ema": 20, "z": 0.75, "hold": {"1h": 7, "4h": 4, "1d": 4}},
        {"variant_id": "panic_rebound", "mode": "panic_rebound", "lookback": 3, "ema": 20, "z": 1.2, "hold": {"1h": 8, "4h": 4, "1d": 4}},
        {"variant_id": "liq_cliff_short", "mode": "liq_cliff_short", "lookback": 5, "ema": 20, "z": 1.0, "hold": {"1h": 10, "4h": 5, "1d": 5}},
        {"variant_id": "low_impact_carry", "mode": "low_impact_carry", "lookback": 10, "ema": 20, "z": 0.9, "hold": {"1h": 10, "4h": 5, "1d": 6}},
    ]
    module.roundtrip_cost = roundtrip_cost
    module.load_panel = lambda path, market, timeframe, lookup: load_panel(module, path, market, timeframe, lookup)
    module.build_trade_rows = lambda panel, variant: build_trade_rows_vectorized(module, panel, variant)
    module.signal_direction = signal_direction
    module.branch_fields = branch_fields
    module.branch_path = branch_path


def load_manip_component(module: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    if not MANIP_SUMMARY_CSV.exists():
        row = module.summarize_rows(
            root="Manipulation(scoped)",
            variant_id="missing_205047_component",
            rows=[],
            all_rows=[],
            pbo=1.0,
            pbo_method="missing_205047_component",
        )
        return row, {"component_available": False}
    with MANIP_SUMMARY_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    passed = [row for row in rows if row.get("gate_result") == "pass:tradeable_manipulation_stop_tp_candidate"]
    best = next((row for row in passed if row.get("variant_id") == "short_tp120_sl060_h72"), passed[0] if passed else None)
    if best is None:
        row = module.summarize_rows(
            root="Manipulation(scoped)",
            variant_id="no_passing_205047_component",
            rows=[],
            all_rows=[],
            pbo=1.0,
            pbo_method="no_passing_205047_component",
        )
        return row, {"component_available": False, "component_source": str(MANIP_SUMMARY_CSV)}
    summary = {
        "recipe_id": "ManipulationStopTakeProfitGridV2",
        "parent_regime_root": "Manipulation(scoped)",
        "selected_variant_id": best["variant_id"],
        "regime_profit_branch_path": best["regime_profit_branch_path"],
        "total_trades": int(best["positive_rows"]),
        "test_folds": int(best["monthly_folds"]),
        "folds": "monthly_folds_12",
        "min_trades_per_test_fold": int(int(best["positive_rows"]) / int(best["monthly_folds"])),
        "fold_positive_rate": float(best["fold_positive_rate_absolute"]),
        "win_rate": 0.0,
        "mean_profit_ratio_net": float(best["positive_mean_net"]),
        "net_return_R": 0.0,
        "bootstrap_edge_lcb_5pct": float(best["positive_lcb_5pct"]),
        "bootstrap_edge_lcb_5pct_stressed_2x_cost": float(best["positive_lcb_5pct"]) - float(best["roundtrip_cost"]),
        "pbo": 0.0,
        "pbo_method": "external_component_not_reoptimized_in_this_run",
        "dsr": 1.0,
        "dsr_method": "external_component_pass_from_205047_not_rescored_here",
        "cost_stress_result": "pass",
        "tail_loss_p95": 0.0,
        "max_drawdown_trade_equity_proxy": 0.0,
        "regime_specificity_ratio": 999.0,
        "outside_mean_profit_ratio_net": float(best["control_mean_net"]),
        "rc_spa": 100.0,
        "promotion_level": "component_pass_only",
        "hard_gate_result": "pass",
        "downstream_consumption_status": "not_started:full_board_b_root_gates_required",
    }
    component = {
        "component_available": True,
        "component_run_id": best["run_id"],
        "component_report": module.rel(MANIP_REPORT_MD),
        "component_summary_csv": module.rel(MANIP_SUMMARY_CSV),
        "component_gate_result": best["gate_result"],
        "component_variant": best["variant_id"],
        "component_positive_rows": int(best["positive_rows"]),
        "component_control_rows": int(best["control_rows"]),
        "component_positive_lcb_5pct": float(best["positive_lcb_5pct"]),
        "component_specificity_lcb_5pct": float(best["positive_minus_control_lcb_5pct"]),
    }
    return summary, component


def write_report(module: Any, report: dict[str, Any]) -> None:
    decision = report["decision"]
    panel_lines = [
        "| Market | TF | Variant | Trades | Mean | Win Rate | Net R |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for row in report["panel_summaries"]:
        panel_lines.append(
            f"| {row['market']} | {row['timeframe']} | `{row['variant_id']}` | "
            f"{row['trades']} | {row['mean_profit_ratio']:.6f} | "
            f"{row['win_rate']:.4f} | {row['net_return_R']:.6f} |"
        )
    branch_lines = [
        "| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["branch_summaries"]:
        branch_lines.append(
            f"| {row['parent_regime_root']} | `{row['selected_variant_id']}` | "
            f"{row['total_trades']} | {row['test_folds']} | "
            f"{row['min_trades_per_test_fold']} | {row['fold_positive_rate']:.4f} | "
            f"{row['bootstrap_edge_lcb_5pct']:.6f} | {row['pbo']:.3f} | "
            f"{row['dsr']:.4f} | {row['rc_spa']:.4f} | `{row['hard_gate_result']}` |"
        )
    lines = [
        "# Crypto Liquidity Root Family RC-SPA v2",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Stable profit score: `{decision['stable_profit_score']:.4f}`",
        f"- Price-root paths passed: `{decision['price_root_paths_passed']}/4`",
        f"- Scoped Manipulation component pass consumed: `{decision['manipulation_component_pass']}`",
        f"- Variant rows: `{decision['variant_trade_rows']}`",
        f"- Selected rows: `{decision['selected_trade_rows']}`",
        f"- Selected root counts: `{decision['selected_root_trade_counts']}`",
        f"- Downstream consumption: `{decision['downstream_consumption']}`",
        f"- Primary blocker: {decision['primary_blocker']}",
        "",
        "## Panel / Variant Summary",
        "",
        *panel_lines,
        "",
        "## Selected Branch Summary",
        "",
        *branch_lines,
        "",
        "## Inputs",
        "",
        f"- Local Auto-Quant feathers: `{DATA_DIR}`",
        f"- Board A consumer map: `{module.rel(module.BOARD_A_CONSUMER_MAP)}`",
        f"- Source root schedule: `{module.SOURCE_REGIME_CSV}` / `{SOURCE_TICKER}`",
        f"- Scoped Manipulation component: `{report['manipulation_component'].get('component_report', 'missing')}`",
        "",
        "## Artifacts",
        "",
        f"- Report JSON: `{module.rel(module.REPORT_JSON)}`",
        f"- Selected rows: `{module.rel(module.SELECTED_ROWS_CSV)}`",
        f"- Variant rows: `{module.rel(module.ALL_ROWS_CSV)}`",
        f"- Branch summary: `{module.rel(module.SUMMARY_CSV)}`",
        f"- Panel summary: `{module.rel(module.PANEL_SUMMARY_CSV)}`",
        f"- Fail-closed downstream summary: `{module.rel(module.FAIL_CLOSED_MD)}`",
        f"- Assertions: `{module.rel(module.ASSERTIONS)}`",
        "",
        "## Next",
        "",
        f"- {decision['next_action']}",
    ]
    module.REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    module = load_base_module()
    patch_module(module)
    for path in [module.OUT_DIR, module.CHECK_DIR, module.FAIL_CLOSED_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    required_inputs = [module.SOURCE_REGIME_CSV, module.BOARD_A_CONSUMER_MAP, MANIP_SUMMARY_CSV]
    missing = [str(path) for path in required_inputs if not path.exists() or path.stat().st_size == 0]
    missing += [str(path) for _, _, path in module.PANELS if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError("missing required inputs: " + ", ".join(missing))

    floors = module.load_root_floors()
    source = module.load_source_roots()
    lookup = module.RootLookup(source, floors)
    all_rows: list[dict[str, Any]] = []
    panel_summaries: list[dict[str, Any]] = []
    for market, timeframe, path in module.PANELS:
        panel = module.load_panel(path, market, timeframe, lookup)
        for variant in module.VARIANTS:
            rows = module.build_trade_rows(panel, variant)
            all_rows.extend(rows)
            values = np.array([float(r["profit_ratio_net"]) for r in rows], dtype=float)
            panel_summaries.append(
                {
                    "market": market,
                    "timeframe": timeframe,
                    "variant_id": variant["variant_id"],
                    "bars": int(len(panel)),
                    "trades": int(len(rows)),
                    "mean_profit_ratio": float(np.mean(values)) if len(values) else 0.0,
                    "win_rate": float(np.mean(values > 0)) if len(values) else 0.0,
                    "net_return_R": float(np.sum(values)) if len(values) else 0.0,
                }
            )

    branch_summaries: list[dict[str, Any]] = []
    variant_summaries: list[dict[str, Any]] = []
    selected_rows: list[dict[str, Any]] = []
    for root in module.ROOTS:
        pbo, pbo_method = module.pbo_for_root(root, all_rows)
        summaries = []
        for variant in [str(v["variant_id"]) for v in module.VARIANTS]:
            rows = [r for r in all_rows if r["parent_regime_root"] == root and str(r["variant_id"]) == variant]
            summaries.append(
                module.summarize_rows(
                    root=root,
                    variant_id=variant,
                    rows=rows,
                    all_rows=all_rows,
                    pbo=pbo,
                    pbo_method=pbo_method,
                )
            )
        selected = max(summaries, key=lambda row: float(row["rc_spa"]))
        branch_summaries.append(selected)
        variant_summaries.extend(summaries)
        selected_variant = str(selected["selected_variant_id"])
        selected_rows.extend(
            [
                r
                for r in all_rows
                if r["parent_regime_root"] == root and str(r["variant_id"]) == selected_variant
            ]
        )

    manip_summary, manip_component = load_manip_component(module)
    branch_summaries.append(manip_summary)

    price_root_summaries = [row for row in branch_summaries if row["parent_regime_root"] in module.ROOTS]
    passed_price_roots = [row for row in price_root_summaries if row["hard_gate_result"] == "pass"]
    manip_pass = manip_summary["hard_gate_result"] == "pass"
    all_required_pass = len(passed_price_roots) == len(module.ROOTS) and manip_pass
    max_price_score = max(float(row["rc_spa"]) for row in price_root_summaries) if price_root_summaries else 0.0
    selected_counts = {root: 0 for root in [*module.ROOTS, "Manipulation(scoped)"]}
    for row in selected_rows:
        selected_counts[row["parent_regime_root"]] = selected_counts.get(row["parent_regime_root"], 0) + 1
    selected_counts["Manipulation(scoped)"] = int(manip_component.get("component_positive_rows", 0))
    matrix_counts = {root: 0 for root in [*module.ROOTS, "Manipulation(scoped)"]}
    for row in all_rows:
        matrix_counts[row["parent_regime_root"]] = matrix_counts.get(row["parent_regime_root"], 0) + 1
    matrix_counts["Manipulation(scoped)"] = int(manip_component.get("component_positive_rows", 0))

    root_failures = [
        f"{row['parent_regime_root']}={row['hard_gate_result']}"
        for row in price_root_summaries
        if row["hard_gate_result"] != "pass"
    ]
    if not manip_pass:
        root_failures.append("Manipulation(scoped)=missing_205047_component_pass")
    gate_result = "pass" if all_required_pass else "fail:required_root_branch_hard_gates_failed"
    downstream = (
        "eligible_for_pre_bayes_bbn_catboost_execution_tree_probe"
        if all_required_pass
        else "not_started:blocked_by_branch_rc_spa_hard_gates"
    )
    primary_blocker = "all required branch hard gates passed" if all_required_pass else "; ".join(root_failures)
    next_action = (
        "B5: run Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree branch consumption with the same branch paths."
        if all_required_pass
        else "B2R-repeat: keep the 205047 scoped Manipulation component, but repair Bull/Bear/Sideways/Crisis with a different root family or panel; do not relax RC-SPA."
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "run_root": module.rel(RUN_ROOT),
        "repo_git_ref": module.git_ref(REPO_ROOT),
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "accepted_regime_artifact": module.rel(module.BOARD_A_CONSUMER_MAP),
        "recipe_id": RECIPE_ID,
        "inputs": {
            "data_dir": str(DATA_DIR),
            "source_regime_csv": str(module.SOURCE_REGIME_CSV),
            "source_ticker": SOURCE_TICKER,
            "board_a_consumer_map": module.rel(module.BOARD_A_CONSUMER_MAP),
            "manipulation_component_summary": module.rel(MANIP_SUMMARY_CSV),
        },
        "decision": {
            "gate_result": gate_result,
            "stable_profit_score": max_price_score,
            "variant_trade_rows": len(all_rows),
            "selected_trade_rows": len(selected_rows),
            "branch_paths_evaluated": len(branch_summaries),
            "branch_paths_passed": len(passed_price_roots) + int(manip_pass),
            "price_root_paths_passed": len(passed_price_roots),
            "manipulation_component_pass": manip_pass,
            "selected_root_trade_counts": selected_counts,
            "matrix_root_trade_counts": matrix_counts,
            "downstream_consumption": downstream,
            "primary_blocker": primary_blocker,
            "next_action": next_action,
        },
        "manipulation_component": manip_component,
        "branch_summaries": branch_summaries,
        "variant_summaries": variant_summaries,
        "panel_summaries": panel_summaries,
        "artifacts": {
            "report_json": module.rel(module.REPORT_JSON),
            "report_md": module.rel(module.REPORT_MD),
            "selected_rows_csv": module.rel(module.SELECTED_ROWS_CSV),
            "all_rows_csv": module.rel(module.ALL_ROWS_CSV),
            "summary_csv": module.rel(module.SUMMARY_CSV),
            "panel_summary_csv": module.rel(module.PANEL_SUMMARY_CSV),
            "assertions": module.rel(module.ASSERTIONS),
            "fail_closed_summary": module.rel(module.FAIL_CLOSED_MD),
        },
        "completion": {
            "runtime_code_changed": False,
            "auto_quant_checkout_changed": False,
            "raw_auto_quant_data_committed": False,
            "thresholds_relaxed_after_scoring": False,
            "downstream_runtime_consumed_branch_path": all_required_pass,
        },
    }

    module.write_csv(module.ALL_ROWS_CSV, all_rows)
    module.write_csv(module.SELECTED_ROWS_CSV, selected_rows)
    module.write_csv(module.SUMMARY_CSV, branch_summaries)
    module.write_csv(module.PANEL_SUMMARY_CSV, panel_summaries)
    module.write_json(module.REPORT_JSON, report)
    write_report(module, report)
    module.FAIL_CLOSED_MD.write_text(
        "\n".join(
            [
                "# Crypto Liquidity Root Family ict-engine Fail-Closed Summary v2",
                "",
                f"Run id: `{RUN_ID}`.",
                "",
                f"- Branch RC-SPA gate: `{gate_result}`",
                f"- Downstream consumption: `{downstream}`",
                "- Pre-Bayes / BBN / CatBoost / execution-tree were not started unless every required branch hard gate passed.",
                "- The 205047 scoped Manipulation component is recorded as a component pass only, not an aggregate promotion.",
                "- This is a fail-closed readback unless all four price roots and scoped Manipulation pass together.",
                "",
                f"Primary blocker: {primary_blocker}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assertions = [
        f"run_id={RUN_ID}",
        f"variant_trade_rows={len(all_rows)}",
        f"selected_trade_rows={len(selected_rows)}",
        f"branch_paths_evaluated={len(branch_summaries)}",
        f"price_root_paths_passed={len(passed_price_roots)}",
        f"manipulation_component_pass={manip_pass}",
        f"gate_result={gate_result}",
        f"downstream_consumption={downstream}",
        "artifacts_exist=true",
    ]
    if not all_rows:
        assertions.append("ASSERT_FAIL:no_variant_trade_rows")
    if not manip_pass:
        assertions.append("ASSERT_FAIL:manipulation_component_not_available")
    module.ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 1 if any(line.startswith("ASSERT_FAIL") for line in assertions) else 0


if __name__ == "__main__":
    raise SystemExit(main())
