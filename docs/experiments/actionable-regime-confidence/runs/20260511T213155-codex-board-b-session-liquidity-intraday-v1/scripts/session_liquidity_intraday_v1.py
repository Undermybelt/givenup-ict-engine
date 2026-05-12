#!/usr/bin/env python3
"""Board B SessionLiquidityIntradayV1 RC-SPA readback.

Run-local artifact script only. It patches the existing Board B RC-SPA
evaluator with a session-window liquidity family over local Auto-Quant
intraday feathers and keeps downstream fail-closed unless every price root
passes unchanged RC-SPA gates.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260511T213155+0800-codex-board-b-session-liquidity-intraday-v1"
SCHEMA_VERSION = "board-b-session-liquidity-intraday/v1"
RECIPE_ID = "SessionLiquidityIntradayV1"
SOURCE_TICKER = "^IXIC"

RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
DATA_DIR = Path("/Users/thrill3r/Auto-Quant/user_data/data")
BASE_SCRIPT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T210508-codex-board-b-crypto-liquidity-root-family-v2/scripts/"
    "crypto_liquidity_root_family_v2.py"
)


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("board_b_crypto_liquidity_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import base evaluator: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def roundtrip_cost(market: str, timeframe: str) -> float:
    if "USDT" in market:
        return 0.0018 if timeframe == "1h" else 0.0015
    if timeframe == "15m":
        return 0.0010
    if timeframe == "1h":
        return 0.0009
    return 0.0008


def branch_path(root: str, variant_id: str) -> str:
    if root == "Bull":
        return f"{root} -> SessionLiquidityExpansion -> WindowMomentumContinuation -> {RECIPE_ID}:{variant_id}"
    if root == "Bear":
        return f"{root} -> SessionLiquidityDrain -> OpenBreakdownOrFailedReclaim -> {RECIPE_ID}:{variant_id}"
    if root == "Sideways":
        return f"{root} -> SessionRangeLiquidity -> IntradayMeanReversion -> {RECIPE_ID}:{variant_id}"
    if root == "Crisis":
        return f"{root} -> SessionStressLiquidity -> TailShortOrPanicReversal -> {RECIPE_ID}:{variant_id}"
    return (
        "Manipulation(scoped) -> TelegramPumpEvent -> ProviderStopTakeShort -> "
        "ManipulationStopTakeProfitGridV2:short_tp120_sl060_h72"
    )


def branch_fields(root: str) -> dict[str, str]:
    if root == "Bull":
        return {
            "sub_regime_tags": "SessionLiquidityExpansion",
            "sub_sub_regime_or_profit_factor": "WindowMomentumContinuation",
            "profit_factor_family": "session_liquidity_intraday",
            "allowed_action": "long_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bull_session_liquidity_branch_rc_spa_fails",
        }
    if root == "Bear":
        return {
            "sub_regime_tags": "SessionLiquidityDrain",
            "sub_sub_regime_or_profit_factor": "OpenBreakdownOrFailedReclaim",
            "profit_factor_family": "session_liquidity_intraday",
            "allowed_action": "short_or_defensive_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bear_session_liquidity_branch_rc_spa_fails",
        }
    if root == "Sideways":
        return {
            "sub_regime_tags": "SessionRangeLiquidity",
            "sub_sub_regime_or_profit_factor": "IntradayMeanReversion",
            "profit_factor_family": "session_liquidity_intraday",
            "allowed_action": "long_short_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_sideways_session_liquidity_branch_rc_spa_fails",
        }
    if root == "Crisis":
        return {
            "sub_regime_tags": "SessionStressLiquidity",
            "sub_sub_regime_or_profit_factor": "TailShortOrPanicReversal",
            "profit_factor_family": "session_liquidity_intraday",
            "allowed_action": "short_or_panic_reversal_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "tail_guard_blocks_session_liquidity_branch_if_rc_spa_fails",
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
    volume_mean = volume.rolling(48, min_periods=12).mean().replace(0, np.nan)
    volume_std = volume.rolling(48, min_periods=12).std().replace(0, np.nan)
    range_pct = ((df["high"] - df["low"]).abs() / df["close"].replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)
    range_mean = range_pct.rolling(48, min_periods=12).mean()
    range_std = range_pct.rolling(48, min_periods=12).std().replace(0, np.nan)
    df["utc_hour"] = pd.to_datetime(df["date"], utc=True).dt.hour.astype(int)
    df["volume_ratio"] = (volume / volume_mean).replace([np.inf, -np.inf], np.nan).fillna(1.0)
    df["volume_z"] = ((volume - volume_mean) / volume_std).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    df["range_pct"] = range_pct.fillna(0.0)
    df["range_z"] = ((range_pct - range_mean) / range_std).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    df["session_bucket"] = df["utc_hour"].map(session_bucket)
    return df


def session_bucket(hour: int) -> str:
    if 0 <= hour <= 6:
        return "asia"
    if 7 <= hour <= 12:
        return "london"
    if 13 <= hour <= 16:
        return "ny_open"
    if 17 <= hour <= 20:
        return "ny_midday"
    return "late"


def _arr(df: pd.DataFrame, column: str) -> np.ndarray:
    return df[column].to_numpy(dtype=float)


def _safe(df: pd.DataFrame, column: str, fallback: str) -> np.ndarray:
    return df[column].to_numpy(dtype=float) if column in df else df[fallback].to_numpy(dtype=float)


def signal_vector(df: pd.DataFrame, variant: dict[str, Any]) -> np.ndarray:
    roots = df["parent_regime_root"].astype(str).to_numpy()
    mode = str(variant["mode"])
    lookback = int(variant["lookback"])
    ema_col = f"ema{int(variant['ema'])}"
    trend = _safe(df, f"ret{lookback}", "ret5")
    ret1 = _arr(df, "ret1")
    ret3 = _arr(df, "ret3")
    z20 = _arr(df, "z20")
    close = _arr(df, "close")
    ema_value = _arr(df, ema_col)
    ema20 = _arr(df, "ema20")
    ema50 = _arr(df, "ema50")
    ema20_slope = _arr(df, "ema20_slope")
    atr_pct = np.maximum(_arr(df, "atr_pct"), 1e-9)
    vix = _arr(df, "source_ticker_vix")
    high20_prev = np.nan_to_num(_arr(df, "high20_prev"), nan=0.0)
    low20_prev = np.nan_to_num(_arr(df, "low20_prev"), nan=0.0)
    volume_ratio = _arr(df, "volume_ratio")
    volume_z = _arr(df, "volume_z")
    range_z = _arr(df, "range_z")
    hour = df["utc_hour"].to_numpy(dtype=int)
    z_threshold = float(variant["z"])
    low_slope = np.abs(ema20_slope) < np.maximum(0.004, atr_pct * 0.35)
    liquidity_expansion = (volume_ratio >= 1.15) | (volume_z >= 0.25)
    liquidity_drain = (volume_ratio <= 0.75) | (range_z >= 0.75)
    ny_open = (hour >= 13) & (hour <= 16)
    london = (hour >= 7) & (hour <= 12)
    asia = (hour <= 6)
    midday = (hour >= 17) & (hour <= 20)
    late = hour >= 21
    signal = np.zeros(len(df), dtype=np.int8)

    bull = roots == "Bull"
    if mode == "london_breakout_follow":
        signal[bull & london & liquidity_expansion & (trend > np.maximum(0.0008, atr_pct * 0.12)) & (close > ema_value)] = 1
    elif mode == "ny_open_pullback_reclaim":
        signal[bull & ny_open & (z20 <= -z_threshold) & (ret1 > -np.maximum(0.002, atr_pct * 0.2)) & (close > ema50)] = 1
    elif mode == "late_session_momentum":
        signal[bull & late & (trend > np.maximum(0.0006, atr_pct * 0.10)) & (close > ema20)] = 1

    bear = roots == "Bear"
    if mode == "ny_open_breakdown_short":
        signal[bear & ny_open & liquidity_expansion & (trend < -np.maximum(0.0008, atr_pct * 0.12)) & (close < ema_value)] = -1
    elif mode == "failed_reclaim_short":
        signal[bear & ((ny_open | london) & (z20 >= z_threshold) & (ret1 < 0) & (close < ema50))] = -1
    elif mode == "liquidity_drain_short":
        signal[bear & liquidity_drain & (trend < 0) & (close < ema20)] = -1

    sideways = roots == "Sideways"
    if mode == "asia_range_reversion":
        signal[sideways & asia & low_slope & (z20 >= z_threshold) & (volume_ratio >= 0.45)] = -1
        signal[sideways & asia & low_slope & (z20 <= -z_threshold) & (volume_ratio >= 0.45)] = 1
    elif mode == "midday_liquidity_reversion":
        signal[sideways & midday & low_slope & (z20 >= z_threshold) & ~liquidity_drain] = -1
        signal[sideways & midday & low_slope & (z20 <= -z_threshold) & ~liquidity_drain] = 1
    elif mode == "range_breakout_failure":
        signal[sideways & low_slope & (close > high20_prev) & (ret1 < 0) & liquidity_expansion] = -1
        signal[sideways & low_slope & (close < low20_prev) & (ret1 > 0) & liquidity_expansion] = 1

    crisis = roots == "Crisis"
    if mode == "crisis_session_tail_short":
        stress = (range_z >= 0.75) | (volume_z >= 0.50) | (vix >= 28)
        signal[crisis & stress & (trend < -np.maximum(0.0008, atr_pct * 0.12)) & (close < ema_value)] = -1
    elif mode == "crisis_panic_reversal":
        panic = (z20 <= -max(1.2, z_threshold)) | (ret3 <= -np.maximum(0.004, atr_pct * 0.80))
        signal[crisis & panic & (ret1 > 0) & liquidity_expansion & (vix < 55)] = 1
    elif mode == "crisis_late_short":
        signal[crisis & late & (trend < 0) & (close < ema20) & ((vix >= 24) | liquidity_drain)] = -1

    return signal


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
    module.ALL_ROWS_CSV = module.OUT_DIR / "session_liquidity_intraday_variant_rows_v1.csv"
    module.SELECTED_ROWS_CSV = module.OUT_DIR / "session_liquidity_intraday_selected_rows_v1.csv"
    module.SUMMARY_CSV = module.OUT_DIR / "session_liquidity_intraday_branch_summary_v1.csv"
    module.PANEL_SUMMARY_CSV = module.OUT_DIR / "session_liquidity_intraday_panel_summary_v1.csv"
    module.REPORT_JSON = module.OUT_DIR / "session_liquidity_intraday_rc_spa_report_v1.json"
    module.REPORT_MD = module.OUT_DIR / "session_liquidity_intraday_rc_spa_report_v1.md"
    module.ASSERTIONS = module.CHECK_DIR / "session_liquidity_intraday_v1_assertions.out"
    module.FAIL_CLOSED_MD = module.FAIL_CLOSED_DIR / "session_liquidity_intraday_fail_closed_summary_v1.md"
    module.PANELS = [
        ("NQ/USD", "15m", DATA_DIR / "NQ_USD-15m.feather"),
        ("NQ/USD", "1h", DATA_DIR / "NQ_USD-1h.feather"),
        ("NQ/USD", "4h", DATA_DIR / "NQ_USD-4h.feather"),
        ("SPY/USD", "15m", DATA_DIR / "SPY_USD-15m.feather"),
        ("SPY/USD", "1h", DATA_DIR / "SPY_USD-1h.feather"),
        ("SPY/USD", "4h", DATA_DIR / "SPY_USD-4h.feather"),
        ("IWM/USD", "15m", DATA_DIR / "IWM_USD-15m.feather"),
        ("IWM/USD", "1h", DATA_DIR / "IWM_USD-1h.feather"),
        ("DIA/USD", "15m", DATA_DIR / "DIA_USD-15m.feather"),
        ("DIA/USD", "1h", DATA_DIR / "DIA_USD-1h.feather"),
        ("GLD/USD", "15m", DATA_DIR / "GLD_USD-15m.feather"),
        ("GLD/USD", "1h", DATA_DIR / "GLD_USD-1h.feather"),
        ("BTC/USDT", "1h", DATA_DIR / "BTC_USDT-1h.feather"),
        ("BTC/USDT", "4h", DATA_DIR / "BTC_USDT-4h.feather"),
        ("ETH/USDT", "1h", DATA_DIR / "ETH_USDT-1h.feather"),
        ("ETH/USDT", "4h", DATA_DIR / "ETH_USDT-4h.feather"),
    ]
    module.VARIANTS = [
        {"variant_id": "london_breakout_follow", "mode": "london_breakout_follow", "lookback": 5, "ema": 20, "z": 0.9, "hold": {"15m": 16, "1h": 8, "4h": 4}},
        {"variant_id": "ny_open_pullback_reclaim", "mode": "ny_open_pullback_reclaim", "lookback": 5, "ema": 20, "z": 0.85, "hold": {"15m": 12, "1h": 6, "4h": 3}},
        {"variant_id": "late_session_momentum", "mode": "late_session_momentum", "lookback": 10, "ema": 20, "z": 0.9, "hold": {"15m": 12, "1h": 6, "4h": 3}},
        {"variant_id": "ny_open_breakdown_short", "mode": "ny_open_breakdown_short", "lookback": 5, "ema": 20, "z": 0.9, "hold": {"15m": 16, "1h": 8, "4h": 4}},
        {"variant_id": "failed_reclaim_short", "mode": "failed_reclaim_short", "lookback": 5, "ema": 20, "z": 0.85, "hold": {"15m": 12, "1h": 6, "4h": 3}},
        {"variant_id": "liquidity_drain_short", "mode": "liquidity_drain_short", "lookback": 10, "ema": 20, "z": 1.0, "hold": {"15m": 16, "1h": 8, "4h": 4}},
        {"variant_id": "asia_range_reversion", "mode": "asia_range_reversion", "lookback": 5, "ema": 20, "z": 0.75, "hold": {"15m": 10, "1h": 5, "4h": 3}},
        {"variant_id": "midday_liquidity_reversion", "mode": "midday_liquidity_reversion", "lookback": 5, "ema": 20, "z": 0.80, "hold": {"15m": 10, "1h": 5, "4h": 3}},
        {"variant_id": "range_breakout_failure", "mode": "range_breakout_failure", "lookback": 5, "ema": 20, "z": 0.75, "hold": {"15m": 12, "1h": 6, "4h": 3}},
        {"variant_id": "crisis_session_tail_short", "mode": "crisis_session_tail_short", "lookback": 5, "ema": 20, "z": 1.0, "hold": {"15m": 16, "1h": 8, "4h": 4}},
        {"variant_id": "crisis_panic_reversal", "mode": "crisis_panic_reversal", "lookback": 3, "ema": 20, "z": 1.1, "hold": {"15m": 12, "1h": 6, "4h": 3}},
        {"variant_id": "crisis_late_short", "mode": "crisis_late_short", "lookback": 5, "ema": 20, "z": 1.0, "hold": {"15m": 12, "1h": 6, "4h": 3}},
    ]
    module.roundtrip_cost = roundtrip_cost
    module.load_panel = lambda path, market, timeframe, lookup: load_panel(module, path, market, timeframe, lookup)
    module.build_trade_rows = lambda panel, variant: module_base.build_trade_rows_vectorized(module, panel, variant)
    module.signal_direction = lambda row, variant: 0
    module.branch_fields = branch_fields
    module.branch_path = branch_path


def postprocess_outputs(module: Any) -> None:
    replacements = {
        "Crypto Liquidity Root Family RC-SPA v2": "Session Liquidity Intraday RC-SPA v1",
        "Crypto Liquidity Root Family ict-engine Fail-Closed Summary v2": "Session Liquidity Intraday ict-engine Fail-Closed Summary v1",
        "crypto liquidity": "session liquidity",
        "crypto-liquidity": "session-liquidity",
    }
    for path in [module.REPORT_MD, module.FAIL_CLOSED_MD]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
    if module.REPORT_JSON.exists():
        report = json.loads(module.REPORT_JSON.read_text(encoding="utf-8"))
        report["artifacts"]["report_md"] = module.rel(module.REPORT_MD)
        module.write_json(module.REPORT_JSON, report)


module_base = load_base_module()


def main() -> int:
    module_base.RUN_ID = RUN_ID
    module_base.SCHEMA_VERSION = SCHEMA_VERSION
    module_base.RECIPE_ID = RECIPE_ID
    module_base.SOURCE_TICKER = SOURCE_TICKER
    module_base.RUN_ROOT = RUN_ROOT
    module_base.REPO_ROOT = REPO_ROOT
    module_base.DATA_DIR = DATA_DIR
    module_base.patch_module = patch_module
    module_base.branch_path = branch_path
    module_base.branch_fields = branch_fields
    module_base.roundtrip_cost = roundtrip_cost
    module_base.signal_vector = signal_vector
    status = int(module_base.main())
    patched_module = module_base.load_base_module()
    patch_module(patched_module)
    postprocess_outputs(patched_module)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
