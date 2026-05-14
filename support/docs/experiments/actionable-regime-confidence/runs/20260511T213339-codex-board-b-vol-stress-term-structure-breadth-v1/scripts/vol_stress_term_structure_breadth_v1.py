#!/usr/bin/env python3
"""Board B volatility-stress breadth RC-SPA readback.

Run-local additive experiment. It reuses the real yfinance daily ETF cache from
the repaired defensive panel, but changes the factor family to volatility
compression/expansion, cross-asset breadth, and stress term-structure proxies.
The 205047 scoped Manipulation branch is consumed only as a component.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260511T213339+0800-codex-board-b-vol-stress-term-structure-breadth-v1"
SCHEMA_VERSION = "board-b-vol-stress-term-structure-breadth/v1"
RECIPE_ID = "VolStressTermStructureBreadthV1"
SOURCE_TICKER = "^GSPC"

RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
PROVIDER_RAW_SCRIPT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T212329-codex-board-b-provider-raw-daily-consensus-v1/scripts/"
    "provider_raw_daily_consensus_v1.py"
)
BASE_CACHE = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T212211-codex-board-b-yfinance-defensive-crossasset-v1-repaired/provider-cache"
)

RISK_ASSETS = {"SPY", "QQQ", "IWM", "DIA", "EFA", "EEM", "HYG", "USO"}
DEFENSIVE_ASSETS = {"TLT", "IEF", "SHY", "GLD", "UUP", "XLU", "XLP", "XLV", "LQD"}
RISK_ONLY = {"SPY", "QQQ", "IWM", "DIA", "EFA", "EEM", "HYG", "USO"}
DEFENSIVE_ONLY = {"TLT", "IEF", "SHY", "GLD", "UUP", "XLU", "XLP", "XLV", "LQD"}

PANELS = [
    (f"{symbol}/YF", "1d", BASE_CACHE / f"{symbol}_USD-1d.feather", symbol)
    for symbol in [
        "SPY",
        "QQQ",
        "IWM",
        "DIA",
        "EFA",
        "EEM",
        "HYG",
        "LQD",
        "TLT",
        "IEF",
        "SHY",
        "GLD",
        "UUP",
        "XLU",
        "XLP",
        "XLV",
        "USO",
    ]
]


def load_provider_raw() -> Any:
    spec = importlib.util.spec_from_file_location("provider_raw_daily_consensus_base", PROVIDER_RAW_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import provider raw wrapper: {PROVIDER_RAW_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _symbol(market: str) -> str:
    return market.split("/", 1)[0]


def read_feather_panel(path: Path) -> pd.DataFrame:
    df = pd.read_feather(path)
    df["date"] = pd.to_datetime(df["date"], unit="ms", utc=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["date", "open", "high", "low", "close"]).sort_values("date").reset_index(drop=True)


def build_cross_sectional_table(module: Any) -> dict[str, pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    for market, _timeframe, path, symbol in PANELS:
        if not path.exists() or path.stat().st_size == 0:
            continue
        df = read_feather_panel(path)
        df = df[(df["date"] >= module.START) & (df["date"] <= module.END)].copy()
        if df.empty:
            continue
        df["session_date"] = df["date"].dt.tz_convert(None).dt.normalize()
        df["ret1"] = df["close"].pct_change().fillna(0.0)
        df["ret5"] = df["close"].pct_change(5).fillna(0.0)
        df["ret20"] = df["close"].pct_change(20).fillna(0.0)
        df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
        df["above_ema50"] = (df["close"] > df["ema50"]).astype(float)
        df["realized_vol20"] = df["ret1"].rolling(20, min_periods=8).std().fillna(0.0)
        frames.append(
            pd.DataFrame(
                {
                    "session_date": df["session_date"],
                    "symbol": symbol,
                    "asset_bucket": "risk" if symbol in RISK_ASSETS else "defensive",
                    "ret1": df["ret1"],
                    "ret5": df["ret5"],
                    "ret20": df["ret20"],
                    "above_ema50": df["above_ema50"],
                    "realized_vol20": df["realized_vol20"],
                }
            )
        )
    if not frames:
        return {}
    all_rows = pd.concat(frames, ignore_index=True)
    pivot_ret20 = all_rows.pivot_table(index="session_date", columns="symbol", values="ret20", aggfunc="last")
    pivot_above = all_rows.pivot_table(index="session_date", columns="symbol", values="above_ema50", aggfunc="last")
    pivot_vol = all_rows.pivot_table(index="session_date", columns="symbol", values="realized_vol20", aggfunc="last")
    risk_cols = [col for col in pivot_ret20.columns if col in RISK_ASSETS]
    defensive_cols = [col for col in pivot_ret20.columns if col in DEFENSIVE_ASSETS]
    out = pd.DataFrame({"session_date": pivot_ret20.index})
    out["risk_ret20_mean"] = pivot_ret20[risk_cols].mean(axis=1).to_numpy(dtype=float)
    out["defensive_ret20_mean"] = pivot_ret20[defensive_cols].mean(axis=1).to_numpy(dtype=float)
    out["risk_minus_defensive_ret20"] = out["risk_ret20_mean"] - out["defensive_ret20_mean"]
    out["risk_breadth_ema50"] = pivot_above[risk_cols].mean(axis=1).to_numpy(dtype=float)
    out["defensive_breadth_ema50"] = pivot_above[defensive_cols].mean(axis=1).to_numpy(dtype=float)
    out["cross_asset_dispersion20"] = pivot_ret20.std(axis=1).fillna(0.0).to_numpy(dtype=float)
    out["panel_realized_vol20_median"] = pivot_vol.median(axis=1).fillna(0.0).to_numpy(dtype=float)
    out["risk_breadth_chg5"] = out["risk_breadth_ema50"].diff(5).fillna(0.0)
    out["vol20_chg5"] = out["panel_realized_vol20_median"].diff(5).fillna(0.0)
    return {"all": out.sort_values("session_date").reset_index(drop=True)}


def roundtrip_cost(market: str, timeframe: str) -> float:
    symbol = _symbol(market)
    if symbol in {"SPY", "QQQ", "DIA", "TLT", "IEF", "SHY"}:
        return 0.00045
    if symbol in {"GLD", "XLU", "XLP", "XLV", "LQD"}:
        return 0.0006
    return 0.0008


def branch_path(root: str, variant_id: str) -> str:
    if root == "Bull":
        return f"{root} -> VolCompressionBreadthRiskOn -> BreadthBreakoutOrPullback -> {RECIPE_ID}:{variant_id}"
    if root == "Bear":
        return f"{root} -> VolExpansionBreadthRiskOff -> DefensiveCarryOrBreakdown -> {RECIPE_ID}:{variant_id}"
    if root == "Sideways":
        return f"{root} -> LowVolRangeBreadthNeutral -> VolBandOrDispersionReversion -> {RECIPE_ID}:{variant_id}"
    if root == "Crisis":
        return f"{root} -> ExtremeVolStress -> TailHedgeBreakdownOrPanicReversal -> {RECIPE_ID}:{variant_id}"
    return (
        "Manipulation(scoped) -> TelegramPumpEvent -> ProviderStopTakeShort -> "
        "ManipulationStopTakeProfitGridV2:short_tp120_sl060_h72"
    )


def branch_fields(root: str) -> dict[str, str]:
    fields = {
        "Bull": (
            "VolCompressionBreadthRiskOn",
            "BreadthBreakoutOrPullback",
            "vol_stress_term_structure_breadth",
            "long_research_only_until_branch_rc_spa_passes",
            "suppress_if_bull_vol_breadth_branch_rc_spa_fails",
        ),
        "Bear": (
            "VolExpansionBreadthRiskOff",
            "DefensiveCarryOrBreakdown",
            "vol_stress_term_structure_breadth",
            "defensive_or_short_research_only_until_branch_rc_spa_passes",
            "suppress_if_bear_vol_breadth_branch_rc_spa_fails",
        ),
        "Sideways": (
            "LowVolRangeBreadthNeutral",
            "VolBandOrDispersionReversion",
            "vol_stress_term_structure_breadth",
            "mean_reversion_research_only_until_branch_rc_spa_passes",
            "suppress_if_sideways_vol_breadth_branch_rc_spa_fails",
        ),
        "Crisis": (
            "ExtremeVolStress",
            "TailHedgeBreakdownOrPanicReversal",
            "vol_stress_term_structure_breadth",
            "tail_hedge_or_short_research_only_until_branch_rc_spa_passes",
            "tail_guard_blocks_crisis_vol_breadth_branch_if_rc_spa_fails",
        ),
    }
    sub, leaf, family, action, suppression = fields.get(
        root,
        (
            "TelegramPumpEvent",
            "ProviderStopTakeShort",
            "direct_manipulation_stop_take_profit",
            "short_stop_tp_component_only",
            "do_not_use_without_price_root_branch_passes",
        ),
    )
    return {
        "sub_regime_tags": sub,
        "sub_sub_regime_or_profit_factor": leaf,
        "profit_factor_family": family,
        "allowed_action": action,
        "suppression_rule": suppression,
    }


def load_panel(module: Any, path: Path, market: str, timeframe: str, lookup: Any) -> pd.DataFrame:
    df = read_feather_panel(path)
    df = df[(df["date"] >= module.START) & (df["date"] <= module.END)].copy()
    if df.empty:
        return df
    df["session_date"] = df["date"].dt.tz_convert(None).dt.normalize()
    root_rows = [lookup.lookup(value) for value in df["session_date"]]
    df = pd.concat([df.reset_index(drop=True), pd.DataFrame(root_rows)], axis=1)
    cross = module.provider_wrapper.CONSENSUS_TABLES.get("all")
    if cross is not None and not cross.empty:
        df = df.merge(cross, on="session_date", how="left")
    for col in [
        "risk_ret20_mean",
        "defensive_ret20_mean",
        "risk_minus_defensive_ret20",
        "risk_breadth_ema50",
        "defensive_breadth_ema50",
        "cross_asset_dispersion20",
        "panel_realized_vol20_median",
        "risk_breadth_chg5",
        "vol20_chg5",
    ]:
        df[col] = pd.to_numeric(df.get(col, 0.0), errors="coerce").fillna(0.0)
    df["provider_id"] = "yfinance_cache_212211"
    df["provider_cluster"] = "vol_stress_breadth_etf_panel"
    df["provider_count"] = len(PANELS)
    df["provider_dispersion"] = df["cross_asset_dispersion20"]
    df["market"] = market
    df["timeframe"] = timeframe
    df["symbol"] = _symbol(market)
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
    df["source_vix_chg5"] = pd.to_numeric(df["source_ticker_vix"], errors="coerce").diff(5).fillna(0.0)
    return df


def signal_vector(df: pd.DataFrame, variant: dict[str, Any]) -> np.ndarray:
    arr = lambda column: df[column].to_numpy(dtype=float)
    roots = df["parent_regime_root"].astype(str).to_numpy()
    symbol = str(df["symbol"].iloc[0])
    mode = str(variant["mode"])
    lookback = int(variant["lookback"])
    trend = arr(f"ret{lookback}" if f"ret{lookback}" in df else "ret5")
    ret1 = arr("ret1")
    ret3 = arr("ret3")
    z20 = arr("z20")
    close = arr("close")
    ema20 = arr("ema20")
    ema50 = arr("ema50")
    ema_slope = arr("ema20_slope")
    atr_pct = np.maximum(arr("atr_pct"), 1e-9)
    vix = arr("source_ticker_vix")
    vix_chg5 = arr("source_vix_chg5")
    risk_breadth = arr("risk_breadth_ema50")
    defensive_breadth = arr("defensive_breadth_ema50")
    risk_minus_def = arr("risk_minus_defensive_ret20")
    dispersion = arr("cross_asset_dispersion20")
    vol20 = arr("panel_realized_vol20_median")
    vol_chg5 = arr("vol20_chg5")
    breadth_chg5 = arr("risk_breadth_chg5")
    z_threshold = float(variant["z"])
    low_slope = np.abs(ema_slope) < np.maximum(0.003, atr_pct * 0.35)
    risk = symbol in RISK_ONLY
    defensive = symbol in DEFENSIVE_ONLY
    signal = np.zeros(len(df), dtype=np.int8)

    bull = roots == "Bull"
    if mode == "breadth_vol_compression_breakout":
        signal[bull & risk & (risk_breadth >= 0.62) & (vol20 < 0.018) & (trend > 0) & (close > ema20) & (vix < 26)] = 1
    elif mode == "breadth_pullback_vix_falling":
        signal[bull & risk & (risk_breadth >= 0.55) & (z20 <= -z_threshold) & (ret1 > 0) & (vix_chg5 <= 0)] = 1
    elif mode == "risk_defense_spread_continuation":
        signal[bull & risk & (risk_minus_def > 0.015) & (breadth_chg5 >= -0.15) & (close > ema50)] = 1

    bear = roots == "Bear"
    if mode == "breadth_breakdown_short":
        signal[bear & risk & (risk_breadth <= 0.45) & (close < ema20) & (trend < -np.maximum(0.004, atr_pct * 0.25))] = -1
    elif mode == "defensive_stress_carry":
        signal[bear & defensive & (defensive_breadth >= 0.50) & (risk_minus_def < 0.0) & (close > ema20)] = 1
    elif mode == "vol_expansion_failed_reclaim_short":
        signal[bear & risk & (vol_chg5 > 0) & (z20 >= z_threshold) & (ret1 < 0) & (close < ema50)] = -1

    sideways = roots == "Sideways"
    if mode == "low_vol_band_reversion":
        signal[sideways & low_slope & (dispersion < 0.035) & (z20 >= z_threshold)] = -1
        signal[sideways & low_slope & (dispersion < 0.035) & (z20 <= -z_threshold)] = 1
    elif mode == "breadth_neutral_range_fade":
        neutral = (risk_breadth >= 0.35) & (risk_breadth <= 0.70) & (np.abs(risk_minus_def) < 0.035)
        signal[sideways & neutral & (close > df["high20_prev"].to_numpy(dtype=float)) & (ret1 < 0)] = -1
        signal[sideways & neutral & (close < df["low20_prev"].to_numpy(dtype=float)) & (ret1 > 0)] = 1
    elif mode == "vol_carry_mean_reversion":
        signal[sideways & defensive & low_slope & (vol20 < 0.020) & (z20 <= -z_threshold)] = 1
        signal[sideways & risk & low_slope & (vol20 < 0.020) & (z20 >= z_threshold)] = -1

    crisis = roots == "Crisis"
    if mode == "crisis_equity_breakdown_short":
        signal[crisis & risk & (vix >= 28) & (ret3 < -np.maximum(0.010, atr_pct * 0.9)) & (close < ema20)] = -1
    elif mode == "crisis_tail_hedge_breakout":
        signal[crisis & defensive & (vix >= 24) & ((close > ema20) | (trend > 0))] = 1
    elif mode == "crisis_panic_reversal":
        signal[crisis & risk & (z20 <= -max(1.5, z_threshold)) & (ret1 > 0) & (vix < 58)] = 1

    return signal


def build_trade_rows(module: Any, provider: Any, panel: pd.DataFrame, variant: dict[str, Any]) -> list[dict[str, Any]]:
    panel = panel.copy()
    if "provider_dispersion" not in panel.columns:
        panel["provider_dispersion"] = pd.to_numeric(panel.get("cross_asset_dispersion20", 0.0), errors="coerce").fillna(0.0)
    if "provider_count" not in panel.columns:
        panel["provider_count"] = len(PANELS)
    if "provider_id" not in panel.columns:
        panel["provider_id"] = "yfinance_cache_212211"
    if "provider_cluster" not in panel.columns:
        panel["provider_cluster"] = "vol_stress_breadth_etf_panel"
    return provider.build_trade_rows(module, panel, variant)


def patch_module(module: Any, provider: Any) -> None:
    provider.RUN_ID = RUN_ID
    provider.SCHEMA_VERSION = SCHEMA_VERSION
    provider.RECIPE_ID = RECIPE_ID
    provider.SOURCE_TICKER = SOURCE_TICKER
    provider.RUN_ROOT = RUN_ROOT
    provider.DATA_DIR = BASE_CACHE
    provider.RAW_PANELS = PANELS
    provider.build_consensus_tables = build_cross_sectional_table
    provider.load_panel = load_panel
    provider.signal_vector = signal_vector
    provider.branch_path = branch_path
    provider.branch_fields = branch_fields
    provider.roundtrip_cost = roundtrip_cost
    provider.write_report = lambda base_module, report: write_report(base_module, report)

    module.provider_wrapper = provider
    module.RUN_ID = RUN_ID
    module.SCHEMA_VERSION = SCHEMA_VERSION
    module.RECIPE_ID = RECIPE_ID
    module.SOURCE_TICKER = SOURCE_TICKER
    module.RUN_ROOT = RUN_ROOT
    module.OUT_DIR = RUN_ROOT / "branch-rc-spa"
    module.CHECK_DIR = RUN_ROOT / "checks"
    module.FAIL_CLOSED_DIR = RUN_ROOT / "ict-engine-fail-closed"
    module.ALL_ROWS_CSV = module.OUT_DIR / "vol_stress_breadth_variant_rows_v1.csv"
    module.SELECTED_ROWS_CSV = module.OUT_DIR / "vol_stress_breadth_selected_rows_v1.csv"
    module.SUMMARY_CSV = module.OUT_DIR / "vol_stress_breadth_branch_summary_v1.csv"
    module.PANEL_SUMMARY_CSV = module.OUT_DIR / "vol_stress_breadth_panel_summary_v1.csv"
    module.REPORT_JSON = module.OUT_DIR / "vol_stress_breadth_rc_spa_report_v1.json"
    module.REPORT_MD = module.OUT_DIR / "vol_stress_breadth_rc_spa_report_v1.md"
    module.ASSERTIONS = module.CHECK_DIR / "vol_stress_breadth_v1_assertions.out"
    module.FAIL_CLOSED_MD = module.FAIL_CLOSED_DIR / "vol_stress_breadth_fail_closed_summary_v1.md"
    module.START = pd.Timestamp("2011-01-01", tz="UTC")
    module.END = pd.Timestamp("2026-01-31", tz="UTC")
    module.PANELS = [(market, timeframe, path) for market, timeframe, path, _symbol in PANELS]
    module.VARIANTS = [
        {"variant_id": "breadth_vol_compression_breakout", "mode": "breadth_vol_compression_breakout", "lookback": 20, "z": 0.95, "hold": {"1d": 5}},
        {"variant_id": "breadth_pullback_vix_falling", "mode": "breadth_pullback_vix_falling", "lookback": 5, "z": 0.85, "hold": {"1d": 4}},
        {"variant_id": "risk_defense_spread_continuation", "mode": "risk_defense_spread_continuation", "lookback": 10, "z": 1.0, "hold": {"1d": 5}},
        {"variant_id": "breadth_breakdown_short", "mode": "breadth_breakdown_short", "lookback": 10, "z": 1.0, "hold": {"1d": 5}},
        {"variant_id": "defensive_stress_carry", "mode": "defensive_stress_carry", "lookback": 10, "z": 0.9, "hold": {"1d": 6}},
        {"variant_id": "vol_expansion_failed_reclaim_short", "mode": "vol_expansion_failed_reclaim_short", "lookback": 5, "z": 0.9, "hold": {"1d": 4}},
        {"variant_id": "low_vol_band_reversion", "mode": "low_vol_band_reversion", "lookback": 5, "z": 0.95, "hold": {"1d": 3}},
        {"variant_id": "breadth_neutral_range_fade", "mode": "breadth_neutral_range_fade", "lookback": 5, "z": 0.75, "hold": {"1d": 4}},
        {"variant_id": "vol_carry_mean_reversion", "mode": "vol_carry_mean_reversion", "lookback": 5, "z": 0.85, "hold": {"1d": 4}},
        {"variant_id": "crisis_equity_breakdown_short", "mode": "crisis_equity_breakdown_short", "lookback": 5, "z": 1.0, "hold": {"1d": 5}},
        {"variant_id": "crisis_tail_hedge_breakout", "mode": "crisis_tail_hedge_breakout", "lookback": 5, "z": 0.9, "hold": {"1d": 6}},
        {"variant_id": "crisis_panic_reversal", "mode": "crisis_panic_reversal", "lookback": 3, "z": 1.25, "hold": {"1d": 3}},
    ]
    module.load_panel = lambda path, market, timeframe, lookup: load_panel(module, path, market, timeframe, lookup)
    module.build_trade_rows = lambda panel, variant: build_trade_rows(module, provider, panel, variant)
    module.branch_path = branch_path
    module.branch_fields = branch_fields


def write_report(module: Any, report: dict[str, Any]) -> None:
    decision = report["decision"]
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
        "# Vol Stress Term-Structure Breadth RC-SPA v1",
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
        "## Selected Branch Summary",
        "",
        *branch_lines,
        "",
        "## Inputs",
        "",
        f"- YFinance daily ETF cache: `{BASE_CACHE}`",
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


def rewrite_fail_closed(report_path: Path, fail_closed_path: Path) -> None:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    decision = report["decision"]
    fail_closed_path.write_text(
        "\n".join(
            [
                "# Vol Stress Term-Structure Breadth ict-engine Fail-Closed Summary v1",
                "",
                f"Run id: `{RUN_ID}`.",
                "",
                f"- Branch RC-SPA gate: `{decision['gate_result']}`",
                f"- Downstream consumption: `{decision['downstream_consumption']}`",
                "- Pre-Bayes / BBN / CatBoost / execution-tree were not started unless every required branch hard gate passed.",
                "- The 205047 scoped Manipulation component is recorded as a component pass only, not an aggregate promotion.",
                "- This is a fail-closed readback unless all four price roots and scoped Manipulation pass together.",
                "",
                f"Primary blocker: {decision['primary_blocker']}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    provider = load_provider_raw()
    base = provider.load_base_module()
    patch_module(base, provider)

    original_load_base = provider.load_base_module
    original_patch_module = provider.patch_module
    provider.load_base_module = lambda: base
    provider.patch_module = lambda module: patch_module(module, provider)
    try:
        code = provider.main()
    finally:
        provider.load_base_module = original_load_base
        provider.patch_module = original_patch_module
    rewrite_fail_closed(base.REPORT_JSON, base.FAIL_CLOSED_MD)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
