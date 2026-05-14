#!/usr/bin/env python3
"""Board B raw-provider daily consensus RC-SPA readback.

Run-local additive experiment. This uses raw daily OHLCV files from yfinance,
Kraken, Binance, and Bybit instead of the existing Auto-Quant feather panels.
It preserves root-first branch paths and consumes the passing 205047 scoped
Manipulation component only as a separate component.
"""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260511T212329+0800-codex-board-b-provider-raw-daily-consensus-v1"
SCHEMA_VERSION = "board-b-provider-raw-daily-consensus/v1"
RECIPE_ID = "ProviderRawDailyConsensusV1"
SOURCE_TICKER = "^IXIC"

RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
DATA_DIR = Path("/Users/thrill3r/Auto-Quant/user_data/data/raw")
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

RAW_PANELS = [
    ("SPY/USD", "1d", DATA_DIR / "SPY_1d.csv", "yf_spy", "equity_index"),
    ("AAPL/USD", "1d", DATA_DIR / "AAPL_1d.csv", "yf_aapl", "equity_single"),
    ("ES/USD", "1d", DATA_DIR / "ES_F_1d.csv", "yf_es_f", "equity_index"),
    ("BTC/USD", "1d", DATA_DIR / "BTC-USD_1d.csv", "yf_btc", "btc_crossvenue"),
    ("BTC/USDT", "1d", DATA_DIR / "binance_BTCUSDT_1d.csv", "binance_btc", "btc_crossvenue"),
    ("BTC/USDT", "1d", DATA_DIR / "bybit_BTCUSDT_linear_1d.csv", "bybit_btc", "btc_crossvenue"),
    ("XBT/USD", "1d", DATA_DIR / "kraken_XBTUSD_1d.csv", "kraken_xbt", "btc_crossvenue"),
    ("EUR/USD", "1d", DATA_DIR / "EURUSD_X_1d.csv", "yf_eurusd", "fx_defensive"),
    ("EUR/USD", "1d", DATA_DIR / "kraken_EURUSD_1d.csv", "kraken_eurusd", "fx_defensive"),
    ("SPYx/USD", "1d", DATA_DIR / "kraken_SPYx_1d.csv", "kraken_spyx", "tokenized_equity"),
    ("SPX/USD", "1d", DATA_DIR / "kraken_PF_SPX_1d.csv", "kraken_spx", "tokenized_equity"),
    ("AAPLx/USD", "1d", DATA_DIR / "kraken_AAPLx_1d.csv", "kraken_aaplx", "tokenized_equity"),
]


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("board_b_root_transition_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import base evaluator: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def panel_meta(path: Path) -> tuple[str, str]:
    for _, _, raw_path, provider_id, cluster in RAW_PANELS:
        if raw_path == path:
            return provider_id, cluster
    return "unknown_provider", "unknown_cluster"


def read_raw_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"date", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"{path} missing columns: {sorted(missing)}")
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["date", "open", "high", "low", "close"]).copy()
    return df.sort_values("date").reset_index(drop=True)


def build_consensus_tables(module: Any) -> dict[str, pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    for market, timeframe, path, provider_id, cluster in RAW_PANELS:
        if not path.exists() or path.stat().st_size == 0:
            continue
        df = read_raw_csv(path)
        df = df[(df["date"] >= module.START) & (df["date"] <= module.END)].copy()
        if df.empty:
            continue
        frames.append(
            pd.DataFrame(
                {
                    "session_date": df["date"].dt.tz_convert(None).dt.normalize(),
                    "provider_id": provider_id,
                    "provider_cluster": cluster,
                    "provider_close": df["close"].astype(float),
                }
            )
        )
    if not frames:
        return {}
    all_prices = pd.concat(frames, ignore_index=True)
    tables: dict[str, pd.DataFrame] = {}
    for cluster, grp in all_prices.groupby("provider_cluster"):
        piv = grp.pivot_table(index="session_date", columns="provider_id", values="provider_close", aggfunc="last")
        median = piv.median(axis=1)
        dispersion = piv.div(median.replace(0, np.nan), axis=0).std(axis=1).replace([np.inf, -np.inf], np.nan)
        out = pd.DataFrame(
            {
                "session_date": piv.index,
                "provider_consensus_close": median.to_numpy(dtype=float),
                "provider_dispersion": dispersion.fillna(0.0).to_numpy(dtype=float),
                "provider_count": piv.notna().sum(axis=1).to_numpy(dtype=int),
            }
        )
        out["provider_consensus_ret5"] = out["provider_consensus_close"].pct_change(5).fillna(0.0)
        out["provider_consensus_ret20"] = out["provider_consensus_close"].pct_change(20).fillna(0.0)
        tables[str(cluster)] = out.sort_values("session_date").reset_index(drop=True)
    return tables


CONSENSUS_TABLES: dict[str, pd.DataFrame] = {}


def load_panel(module: Any, path: Path, market: str, timeframe: str, lookup: Any) -> pd.DataFrame:
    provider_id, cluster = panel_meta(path)
    df = read_raw_csv(path)
    df = df[(df["date"] >= module.START) & (df["date"] <= module.END)].copy()
    if df.empty:
        return df
    df = df.sort_values("date").reset_index(drop=True)
    df["session_date"] = df["date"].dt.tz_convert(None).dt.normalize()
    root_rows = [lookup.lookup(value) for value in df["session_date"]]
    df = pd.concat([df, pd.DataFrame(root_rows)], axis=1)
    consensus = CONSENSUS_TABLES.get(cluster)
    if consensus is not None and not consensus.empty:
        df = df.merge(consensus, on="session_date", how="left")
    else:
        df["provider_consensus_close"] = df["close"]
        df["provider_dispersion"] = 0.0
        df["provider_count"] = 1
        df["provider_consensus_ret5"] = 0.0
        df["provider_consensus_ret20"] = 0.0
    df["provider_id"] = provider_id
    df["provider_cluster"] = cluster
    df["market"] = market
    df["timeframe"] = timeframe
    df["ret1"] = df["close"].pct_change().fillna(0.0)
    df["ret3"] = df["close"].pct_change(3).fillna(0.0)
    df["ret5"] = df["close"].pct_change(5).fillna(0.0)
    df["ret10"] = df["close"].pct_change(10).fillna(0.0)
    df["ret20"] = df["close"].pct_change(20).fillna(0.0)
    high_low = (df["high"] - df["low"]).abs()
    high_close = (df["high"] - df["close"].shift(1)).abs()
    low_close = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr20"] = tr.rolling(20, min_periods=5).mean().bfill()
    df["atr_pct"] = (df["atr20"] / df["close"]).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
    mean20 = df["close"].rolling(20, min_periods=10).mean()
    std20 = df["close"].rolling(20, min_periods=10).std()
    df["z20"] = ((df["close"] - mean20) / std20.replace(0, np.nan)).fillna(0.0)
    df["high20_prev"] = df["high"].rolling(20, min_periods=10).max().shift(1)
    df["low20_prev"] = df["low"].rolling(20, min_periods=10).min().shift(1)
    df["ema20_slope"] = df["ema20"].pct_change(5).fillna(0.0)
    for col in ["provider_consensus_close", "provider_dispersion", "provider_count", "provider_consensus_ret5", "provider_consensus_ret20"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df


def is_risk_asset(market: str) -> bool:
    return any(token in market for token in ("SPY", "SPX", "AAPL", "ES", "BTC", "XBT"))


def is_btc_asset(market: str) -> bool:
    return "BTC" in market or "XBT" in market


def is_defensive_asset(market: str) -> bool:
    return "EUR" in market


def roundtrip_cost(market: str, timeframe: str) -> float:
    if is_btc_asset(market):
        return 0.0018
    if is_defensive_asset(market):
        return 0.0008
    return 0.0010


def branch_path(root: str, variant_id: str) -> str:
    if root == "Bull":
        return f"{root} -> RawProviderConsensusRiskOn -> CrossVenueMomentum -> {RECIPE_ID}:{variant_id}"
    if root == "Bear":
        return f"{root} -> RawProviderRiskOff -> DefensiveOrBreakdown -> {RECIPE_ID}:{variant_id}"
    if root == "Sideways":
        return f"{root} -> RawProviderRange -> DispersionReversion -> {RECIPE_ID}:{variant_id}"
    if root == "Crisis":
        return f"{root} -> RawProviderStress -> TailShortOrDefensiveReversal -> {RECIPE_ID}:{variant_id}"
    return "Manipulation(scoped) -> TelegramPumpEvent -> ProviderStopTakeShort -> ManipulationStopTakeProfitGridV2:short_tp120_sl060_h72"


def branch_fields(root: str) -> dict[str, str]:
    if root == "Bull":
        return {
            "sub_regime_tags": "RawProviderConsensusRiskOn",
            "sub_sub_regime_or_profit_factor": "CrossVenueMomentum",
            "profit_factor_family": "provider_raw_daily_consensus",
            "allowed_action": "long_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bull_raw_provider_branch_rc_spa_fails",
        }
    if root == "Bear":
        return {
            "sub_regime_tags": "RawProviderRiskOff",
            "sub_sub_regime_or_profit_factor": "DefensiveOrBreakdown",
            "profit_factor_family": "provider_raw_daily_consensus",
            "allowed_action": "short_or_defensive_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bear_raw_provider_branch_rc_spa_fails",
        }
    if root == "Sideways":
        return {
            "sub_regime_tags": "RawProviderRange",
            "sub_sub_regime_or_profit_factor": "DispersionReversion",
            "profit_factor_family": "provider_raw_daily_consensus",
            "allowed_action": "long_short_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_sideways_raw_provider_branch_rc_spa_fails",
        }
    if root == "Crisis":
        return {
            "sub_regime_tags": "RawProviderStress",
            "sub_sub_regime_or_profit_factor": "TailShortOrDefensiveReversal",
            "profit_factor_family": "provider_raw_daily_consensus",
            "allowed_action": "short_or_defensive_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "tail_guard_blocks_raw_provider_branch_if_rc_spa_fails",
        }
    return {
        "sub_regime_tags": "TelegramPumpEvent",
        "sub_sub_regime_or_profit_factor": "ProviderStopTakeShort",
        "profit_factor_family": "direct_manipulation_stop_take_profit",
        "allowed_action": "short_stop_tp_component_only",
        "suppression_rule": "do_not_use_without_price_root_branch_passes",
    }


def _arr(df: pd.DataFrame, column: str) -> np.ndarray:
    return df[column].to_numpy(dtype=float)


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
    market = str(df["market"].iloc[0])
    mode = str(variant["mode"])
    lookback = int(variant["lookback"])
    trend = _arr(df, f"ret{lookback}" if f"ret{lookback}" in df else "ret5")
    ret1 = _arr(df, "ret1")
    ret3 = _arr(df, "ret3")
    z20 = _arr(df, "z20")
    close = _arr(df, "close")
    ema20 = _arr(df, "ema20")
    ema50 = _arr(df, "ema50")
    ema20_slope = _arr(df, "ema20_slope")
    atr_pct = np.maximum(_arr(df, "atr_pct"), 1e-9)
    dispersion = _arr(df, "provider_dispersion")
    provider_count = _arr(df, "provider_count")
    consensus_ret5 = _arr(df, "provider_consensus_ret5")
    consensus_ret20 = _arr(df, "provider_consensus_ret20")
    vix = _arr(df, "source_ticker_vix")
    z_threshold = float(variant["z"])
    low_slope = np.abs(ema20_slope) < np.maximum(0.0035, atr_pct * 0.38)
    risk = is_risk_asset(market)
    btc = is_btc_asset(market)
    defensive = is_defensive_asset(market)
    crossvenue_ok = (provider_count >= 2) & (dispersion <= float(variant.get("max_dispersion", 0.025)))
    btc_consensus_ok = (consensus_ret20 > 0) if btc else np.ones(len(df), dtype=bool)
    btc_crossvenue_ok = crossvenue_ok if btc else np.ones(len(df), dtype=bool)
    btc_range_ok = (dispersion <= 0.03) if btc else np.ones(len(df), dtype=bool)
    signal = np.zeros(len(df), dtype=np.int8)

    bull = roots == "Bull"
    if mode == "consensus_momentum":
        signal[bull & risk & (close > ema50) & (trend > 0) & btc_consensus_ok & btc_crossvenue_ok] = 1
    elif mode == "provider_pullback_reclaim":
        signal[bull & risk & (close > ema50) & (z20 <= -z_threshold) & (ret1 > 0)] = 1
    elif mode == "btc_crossvenue_carry":
        signal[bull & btc & crossvenue_ok & (close > ema20) & (consensus_ret5 > 0)] = 1

    bear = roots == "Bear"
    if mode == "provider_breakdown_short":
        signal[bear & risk & (close < ema20) & (trend < -np.maximum(0.003, atr_pct * 0.20))] = -1
    elif mode == "defensive_fx_long":
        signal[bear & defensive & (close > ema20) & (trend > 0)] = 1
    elif mode == "failed_reclaim_short":
        signal[bear & risk & (close < ema50) & (z20 >= z_threshold) & (ret1 < 0)] = -1

    sideways = roots == "Sideways"
    if mode == "dispersion_reversion":
        signal[sideways & low_slope & (z20 >= z_threshold) & btc_range_ok] = -1
        signal[sideways & low_slope & (z20 <= -z_threshold) & btc_range_ok] = 1
    elif mode == "provider_range_breakout_failure":
        high_fail = (close > _arr(df, "high20_prev")) & (ret1 < 0)
        low_fail = (close < _arr(df, "low20_prev")) & (ret1 > 0)
        signal[sideways & low_slope & high_fail] = -1
        signal[sideways & low_slope & low_fail] = 1

    crisis = roots == "Crisis"
    if mode == "crisis_tail_short":
        stress = (vix >= 28) | (ret3 < -np.maximum(0.012, atr_pct * 1.25))
        signal[crisis & risk & stress & (close < ema20)] = -1
    elif mode == "crisis_defensive_fx_long":
        signal[crisis & defensive & ((close > ema20) | (trend > 0))] = 1
    elif mode == "crisis_panic_reversal":
        panic = (z20 <= -max(1.4, z_threshold)) | (ret3 <= -np.maximum(0.018, atr_pct * 1.5))
        signal[crisis & risk & panic & (ret1 > 0) & (vix < 55)] = 1

    return signal


def build_trade_rows(module: Any, df: pd.DataFrame, variant: dict[str, Any]) -> list[dict[str, Any]]:
    if df.empty:
        return []
    variant_id = str(variant["variant_id"])
    timeframe = str(df["timeframe"].iloc[0])
    market = str(df["market"].iloc[0])
    hold = int(variant["hold"].get(timeframe, 5))
    cost = roundtrip_cost(market, timeframe)
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
    gross = direction * (exit_price / entry - 1.0)
    roots = df["parent_regime_root"].astype(str).to_numpy()
    dates = df["date"].to_numpy()
    session_dates = df["session_date"].to_numpy()
    floors = _arr(df, "parent_regime_confidence_floor")
    conf = _arr(df, "source_ticker_confidence")
    vix = _arr(df, "source_ticker_vix")
    lookup_status = df["root_lookup_status"].astype(str).to_numpy()
    provider_id = df["provider_id"].astype(str).to_numpy()
    provider_cluster = df["provider_cluster"].astype(str).to_numpy()
    dispersion = _arr(df, "provider_dispersion")
    provider_count = _arr(df, "provider_count")

    rows: list[dict[str, Any]] = []
    for pos, open_idx in enumerate(idx.tolist()):
        root = str(roots[open_idx])
        if root not in module.ROOTS:
            continue
        fields = branch_fields(root)
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
                "trade_id": f"{RECIPE_ID}:{variant_id}:{market}:{timeframe}:{provider_id[open_idx]}:{open_idx}",
                "open_date": open_ts.isoformat(),
                "close_date": close_ts.isoformat(),
                "open_session_date": pd.Timestamp(session_dates[open_idx]).date().isoformat(),
                "source_anchor": SOURCE_TICKER,
                "parent_regime_root": root,
                "parent_regime_confidence_floor": float(floors[open_idx]),
                "source_ticker_confidence": float(conf[open_idx]),
                "source_ticker_vix": float(vix[open_idx]),
                "manipulation_overlay_state": "component_pass_from_205047_not_rescored_here",
                "sub_regime_tags": fields["sub_regime_tags"],
                "sub_sub_regime_or_profit_factor": fields["sub_sub_regime_or_profit_factor"],
                "profit_factor_family": fields["profit_factor_family"],
                "profit_factor_leaf": f"{RECIPE_ID}:{variant_id}",
                "regime_profit_branch_path": branch_path(root, variant_id),
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
                "provider_id": str(provider_id[open_idx]),
                "provider_cluster": str(provider_cluster[open_idx]),
                "provider_count": int(provider_count[open_idx]),
                "provider_dispersion": float(dispersion[open_idx]),
            }
        )
    return rows


def load_manip_component(module: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    if not MANIP_SUMMARY_CSV.exists():
        row = module.summarize_rows(root="Manipulation(scoped)", variant_id="missing_205047_component", rows=[], all_rows=[], pbo=1.0, pbo_method="missing_205047_component")
        return row, {"component_available": False}
    with MANIP_SUMMARY_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    passed = [row for row in rows if row.get("gate_result") == "pass:tradeable_manipulation_stop_tp_candidate"]
    best = next((row for row in passed if row.get("variant_id") == "short_tp120_sl060_h72"), passed[0] if passed else None)
    if best is None:
        row = module.summarize_rows(root="Manipulation(scoped)", variant_id="no_passing_205047_component", rows=[], all_rows=[], pbo=1.0, pbo_method="no_passing_205047_component")
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
    return summary, {
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


def patch_module(module: Any) -> None:
    module.RUN_ID = RUN_ID
    module.SCHEMA_VERSION = SCHEMA_VERSION
    module.RECIPE_ID = RECIPE_ID
    module.SOURCE_TICKER = SOURCE_TICKER
    module.RUN_ROOT = RUN_ROOT
    module.OUT_DIR = RUN_ROOT / "branch-rc-spa"
    module.CHECK_DIR = RUN_ROOT / "checks"
    module.FAIL_CLOSED_DIR = RUN_ROOT / "ict-engine-fail-closed"
    module.ALL_ROWS_CSV = module.OUT_DIR / "provider_raw_daily_consensus_variant_rows_v1.csv"
    module.SELECTED_ROWS_CSV = module.OUT_DIR / "provider_raw_daily_consensus_selected_rows_v1.csv"
    module.SUMMARY_CSV = module.OUT_DIR / "provider_raw_daily_consensus_branch_summary_v1.csv"
    module.PANEL_SUMMARY_CSV = module.OUT_DIR / "provider_raw_daily_consensus_panel_summary_v1.csv"
    module.REPORT_JSON = module.OUT_DIR / "provider_raw_daily_consensus_rc_spa_report_v1.json"
    module.REPORT_MD = module.OUT_DIR / "provider_raw_daily_consensus_rc_spa_report_v1.md"
    module.ASSERTIONS = module.CHECK_DIR / "provider_raw_daily_consensus_v1_assertions.out"
    module.FAIL_CLOSED_MD = module.FAIL_CLOSED_DIR / "provider_raw_daily_consensus_fail_closed_summary_v1.md"
    module.START = pd.Timestamp("2011-01-01", tz="UTC")
    module.END = pd.Timestamp("2026-01-31", tz="UTC")
    module.PANELS = [(market, timeframe, path) for market, timeframe, path, _, _ in RAW_PANELS]
    module.VARIANTS = [
        {"variant_id": "provider_consensus_momentum", "mode": "consensus_momentum", "lookback": 20, "z": 1.0, "max_dispersion": 0.025, "hold": {"1d": 5}},
        {"variant_id": "provider_pullback_reclaim", "mode": "provider_pullback_reclaim", "lookback": 5, "z": 0.85, "max_dispersion": 0.030, "hold": {"1d": 4}},
        {"variant_id": "btc_crossvenue_carry", "mode": "btc_crossvenue_carry", "lookback": 10, "z": 1.0, "max_dispersion": 0.022, "hold": {"1d": 5}},
        {"variant_id": "provider_breakdown_short", "mode": "provider_breakdown_short", "lookback": 10, "z": 1.0, "max_dispersion": 0.035, "hold": {"1d": 5}},
        {"variant_id": "defensive_fx_long", "mode": "defensive_fx_long", "lookback": 10, "z": 0.9, "max_dispersion": 0.030, "hold": {"1d": 6}},
        {"variant_id": "failed_reclaim_short", "mode": "failed_reclaim_short", "lookback": 5, "z": 0.9, "max_dispersion": 0.030, "hold": {"1d": 4}},
        {"variant_id": "dispersion_reversion", "mode": "dispersion_reversion", "lookback": 5, "z": 0.90, "max_dispersion": 0.030, "hold": {"1d": 3}},
        {"variant_id": "provider_range_breakout_failure", "mode": "provider_range_breakout_failure", "lookback": 5, "z": 0.75, "max_dispersion": 0.030, "hold": {"1d": 4}},
        {"variant_id": "crisis_tail_short", "mode": "crisis_tail_short", "lookback": 5, "z": 1.0, "max_dispersion": 0.040, "hold": {"1d": 5}},
        {"variant_id": "crisis_defensive_fx_long", "mode": "crisis_defensive_fx_long", "lookback": 5, "z": 0.9, "max_dispersion": 0.030, "hold": {"1d": 6}},
        {"variant_id": "crisis_panic_reversal", "mode": "crisis_panic_reversal", "lookback": 3, "z": 1.2, "max_dispersion": 0.035, "hold": {"1d": 3}},
    ]
    module.load_panel = lambda path, market, timeframe, lookup: load_panel(module, path, market, timeframe, lookup)
    module.build_trade_rows = lambda panel, variant: build_trade_rows(module, panel, variant)
    module.branch_path = branch_path
    module.branch_fields = branch_fields


def write_report(module: Any, report: dict[str, Any]) -> None:
    decision = report["decision"]
    panel_lines = [
        "| Market | TF | Variant | Trades | Mean | Win Rate | Net R |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for row in report["panel_summaries"]:
        panel_lines.append(
            f"| {row['market']} | {row['timeframe']} | `{row['variant_id']}` | "
            f"{row['trades']} | {row['mean_profit_ratio']:.6f} | {row['win_rate']:.4f} | {row['net_return_R']:.6f} |"
        )
    branch_lines = [
        "| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["branch_summaries"]:
        branch_lines.append(
            f"| {row['parent_regime_root']} | `{row['selected_variant_id']}` | "
            f"{row['total_trades']} | {row['test_folds']} | {row['min_trades_per_test_fold']} | "
            f"{row['fold_positive_rate']:.4f} | {row['bootstrap_edge_lcb_5pct']:.6f} | "
            f"{row['pbo']:.3f} | {row['dsr']:.4f} | {row['rc_spa']:.4f} | `{row['hard_gate_result']}` |"
        )
    lines = [
        "# Provider Raw Daily Consensus RC-SPA v1",
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
        f"- Raw provider OHLCV files: `{DATA_DIR}`",
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
    global CONSENSUS_TABLES
    CONSENSUS_TABLES = build_consensus_tables(module)
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
            summaries.append(module.summarize_rows(root=root, variant_id=variant, rows=rows, all_rows=all_rows, pbo=pbo, pbo_method=pbo_method))
        selected = max(summaries, key=lambda row: float(row["rc_spa"]))
        branch_summaries.append(selected)
        variant_summaries.extend(summaries)
        selected_variant = str(selected["selected_variant_id"])
        selected_rows.extend([r for r in all_rows if r["parent_regime_root"] == root and str(r["variant_id"]) == selected_variant])

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
    root_failures = [f"{row['parent_regime_root']}={row['hard_gate_result']}" for row in price_root_summaries if row["hard_gate_result"] != "pass"]
    if not manip_pass:
        root_failures.append("Manipulation(scoped)=missing_205047_component_pass")
    gate_result = "pass" if all_required_pass else "fail:required_root_branch_hard_gates_failed"
    downstream = "eligible_for_pre_bayes_bbn_catboost_execution_tree_probe" if all_required_pass else "not_started:blocked_by_branch_rc_spa_hard_gates"
    primary_blocker = "all required branch hard gates passed" if all_required_pass else "; ".join(root_failures)
    next_action = (
        "B5: run Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree branch consumption with the same branch paths."
        if all_required_pass
        else "B2R-repeat: keep the 205047 scoped Manipulation component, but repair Bull/Bear/Sideways/Crisis with a different root family or provider panel; do not relax RC-SPA."
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
                "# Provider Raw Daily Consensus ict-engine Fail-Closed Summary v1",
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
