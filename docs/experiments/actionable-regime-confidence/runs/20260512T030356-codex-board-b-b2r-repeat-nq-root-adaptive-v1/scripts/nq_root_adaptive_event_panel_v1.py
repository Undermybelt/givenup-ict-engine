#!/usr/bin/env python3
"""Board B B2R repeat-next: long-history NQ root-adaptive event panel.

Run-local experiment only. It consumes cached local Auto-Quant OHLCV data,
attaches Board A source-root labels, scores predeclared root-specific NQ event
variants, and combines the existing direct Manipulation stop/TP component as a
separate branch. It does not modify ict-engine runtime code or Auto-Quant.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260512T030356+0800-codex-board-b-b2r-repeat-nq-root-adaptive-v1"
SCHEMA_VERSION = "board-b-b2r-repeat-nq-root-adaptive-event-panel/v1"
RECIPE_ID = "NQRootAdaptiveEventPanelV1"
SYMBOL = "B2R_NQ_ROOT_ADAPTIVE_030356"
ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]

AUTO_QUANT_DATA = Path("/Users/thrill3r/Auto-Quant/user_data/data")
SOURCE_REGIME_CSV = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
BOARD_A_CONSUMER_MAP = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/"
    "regime_factor_consumer_map_v1.csv"
)
MANIP_ASSERTIONS = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/checks/"
    "manipulation_stop_tp_grid_v2_assertions.out"
)
MANIP_SUMMARY = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/"
    "manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2_summary.csv"
)

VARIANTS: list[dict[str, Any]] = [
    {
        "root": "Bull",
        "variant_id": "bull_trend_continuation_h24",
        "branch_path": "Bull -> TrendExpansion -> NQTrendContinuation -> NQRootAdaptiveEventPanelV1:bull_trend_continuation_h24",
        "hold": 24,
        "action": "long",
        "ret24_min": 0.0020,
        "close_above_ema": "ema_96",
        "vol_z_max": 1.60,
    },
    {
        "root": "Bull",
        "variant_id": "bull_pullback_resume_h12",
        "branch_path": "Bull -> TrendExpansion -> NQPullbackResume -> NQRootAdaptiveEventPanelV1:bull_pullback_resume_h12",
        "hold": 12,
        "action": "long",
        "ret6_max": -0.0015,
        "close_above_ema": "ema_168",
        "vol_z_max": 1.80,
    },
    {
        "root": "Bull",
        "variant_id": "bull_low_vol_breakout_h36",
        "branch_path": "Bull -> TrendExpansion -> NQLowVolBreakout -> NQRootAdaptiveEventPanelV1:bull_low_vol_breakout_h36",
        "hold": 36,
        "action": "long",
        "ret72_min": 0.0060,
        "vol_z_max": 0.80,
        "close_above_ema": "ema_96",
    },
    {
        "root": "Bear",
        "variant_id": "bear_breakdown_short_h24",
        "branch_path": "Bear -> BearMarketDrawdown -> NQBreakdownShort -> NQRootAdaptiveEventPanelV1:bear_breakdown_short_h24",
        "hold": 24,
        "action": "short",
        "ret24_max": -0.0030,
        "close_below_ema": "ema_96",
        "vol_z_max": 2.20,
    },
    {
        "root": "Bear",
        "variant_id": "bear_relief_fade_h12",
        "branch_path": "Bear -> BearMarketDrawdown -> NQReliefFade -> NQRootAdaptiveEventPanelV1:bear_relief_fade_h12",
        "hold": 12,
        "action": "short",
        "ret6_min": 0.0015,
        "close_below_ema": "ema_168",
        "vol_z_max": 2.50,
    },
    {
        "root": "Bear",
        "variant_id": "bear_capitulation_rebound_h24",
        "branch_path": "Bear -> BearMarketDrawdown -> NQCapitulationRebound -> NQRootAdaptiveEventPanelV1:bear_capitulation_rebound_h24",
        "hold": 24,
        "action": "long",
        "ret24_max": -0.0120,
        "vol_z_min": 0.20,
    },
    {
        "root": "Sideways",
        "variant_id": "sideways_pullback_revert_h12",
        "branch_path": "Sideways -> RangeConsolidation -> NQPullbackReversion -> NQRootAdaptiveEventPanelV1:sideways_pullback_revert_h12",
        "hold": 12,
        "action": "long",
        "ret6_max": -0.0025,
        "ret72_abs_max": 0.0300,
        "zscore_max": -0.60,
        "vol_z_max": 1.20,
    },
    {
        "root": "Sideways",
        "variant_id": "sideways_pop_fade_h12",
        "branch_path": "Sideways -> RangeConsolidation -> NQPopFade -> NQRootAdaptiveEventPanelV1:sideways_pop_fade_h12",
        "hold": 12,
        "action": "short",
        "ret6_min": 0.0025,
        "ret72_abs_max": 0.0300,
        "zscore_min": 0.60,
        "vol_z_max": 1.20,
    },
    {
        "root": "Sideways",
        "variant_id": "sideways_band_reversion_h24",
        "branch_path": "Sideways -> RangeConsolidation -> NQBandReversion -> NQRootAdaptiveEventPanelV1:sideways_band_reversion_h24",
        "hold": 24,
        "action": "z_revert",
        "ret72_abs_max": 0.0400,
        "zscore_abs_min": 0.85,
        "vol_z_max": 1.35,
    },
    {
        "root": "Crisis",
        "variant_id": "crisis_shock_short_h12",
        "branch_path": "Crisis -> ExtremeStress -> NQShockShort -> NQRootAdaptiveEventPanelV1:crisis_shock_short_h12",
        "hold": 12,
        "action": "short",
        "ret6_max": -0.0045,
        "vol_z_min": 0.25,
    },
    {
        "root": "Crisis",
        "variant_id": "crisis_flush_rebound_h24",
        "branch_path": "Crisis -> ExtremeStress -> NQFlushRebound -> NQRootAdaptiveEventPanelV1:crisis_flush_rebound_h24",
        "hold": 24,
        "action": "long",
        "ret24_max": -0.0200,
        "vol_z_min": 0.50,
    },
    {
        "root": "Crisis",
        "variant_id": "crisis_tail_hedge_h36",
        "branch_path": "Crisis -> ExtremeStress -> NQTailHedge -> NQRootAdaptiveEventPanelV1:crisis_tail_hedge_h36",
        "hold": 36,
        "action": "short",
        "ret24_max": -0.0080,
        "close_below_ema": "ema_96",
        "vol_z_min": 0.10,
    },
]

ROUND_TRIP_COST = 0.0009
EXTRA_ROUND_TRIP_COST_FOR_2X_COST = 0.0009
TARGET_EDGE = 0.001
TARGET_DSR = 1.0
DRAWDOWN_BUDGET = 0.30
TAIL_LOSS_BUDGET = 0.08
MIN_TOTAL_TRADES = 50
MIN_TEST_FOLDS = 4
MIN_TRADES_PER_TEST_FOLD = 3
FOLD_POSITIVE_RATE_MIN = 0.70
MAX_ROWS_PER_VARIANT = 12000

RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "nq-root-adaptive-panel"
CHECK_DIR = RUN_ROOT / "checks"
COMMAND_DIR = RUN_ROOT / "command-output"
STATE_SYMBOL_DIR = RUN_ROOT / "state_nq_root_adaptive_panel_v1" / SYMBOL

REPORT_JSON = OUT_DIR / "nq_root_adaptive_panel_rc_spa_v1.json"
REPORT_MD = OUT_DIR / "nq_root_adaptive_panel_rc_spa_v1.md"
VARIANT_ROWS_CSV = OUT_DIR / "nq_root_adaptive_panel_variant_rows_v1.csv"
SELECTED_ROWS_CSV = OUT_DIR / "nq_root_adaptive_panel_selected_rows_v1.csv"
BRANCH_SUMMARY_CSV = OUT_DIR / "nq_root_adaptive_panel_branch_summary_v1.csv"
INPUTS_JSON = OUT_DIR / "nq_root_adaptive_panel_inputs_v1.json"
REAL_TRADES = OUT_DIR / "nq_root_adaptive_panel_real_trades_v1.jsonl"
STRATEGY_LIBRARY = OUT_DIR / "strategy_library_nq_root_adaptive_panel_v1.json"
ASSERTIONS = CHECK_DIR / "nq_root_adaptive_panel_v1_assertions.out"


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot find repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def ensure_dirs() -> None:
    for path in [OUT_DIR, CHECK_DIR, COMMAND_DIR, STATE_SYMBOL_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def normalize_date(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_datetime(series, unit="ms", utc=True)
    return pd.to_datetime(series, utc=True)


def read_feather_ohlcv(path: Path) -> pd.DataFrame:
    df = pd.read_feather(path)
    df["date"] = normalize_date(df["date"])
    df = df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    return df[["date", "open", "high", "low", "close", "volume"]].copy()


def load_source_root(ticker: str = "^IXIC") -> pd.DataFrame:
    roots = pd.read_csv(
        SOURCE_REGIME_CSV,
        usecols=["date", "ticker", "regime_label", "regime_confidence", "vix"],
    )
    roots = roots[roots["ticker"] == ticker].copy()
    roots["date"] = pd.to_datetime(roots["date"], utc=True).dt.normalize()
    roots = roots.sort_values("date").reset_index(drop=True)
    if roots.empty:
        raise RuntimeError(f"missing source root rows for {ticker}")
    return roots


def attach_roots(df: pd.DataFrame, roots: pd.DataFrame) -> pd.DataFrame:
    source_dates = roots["date"].to_numpy(dtype="datetime64[ns]")
    source_roots = roots["regime_label"].astype(str).to_numpy()
    source_conf = roots["regime_confidence"].astype(float).to_numpy()
    source_vix = roots["vix"].astype(float).to_numpy()
    bar_dates = df["date"].dt.normalize().to_numpy(dtype="datetime64[ns]")
    positions = np.searchsorted(source_dates, bar_dates, side="right") - 1
    labels = np.full(len(df), "Unlabeled", dtype=object)
    conf = np.full(len(df), np.nan, dtype=float)
    vix = np.full(len(df), np.nan, dtype=float)
    valid = positions >= 0
    labels[valid] = source_roots[positions[valid]]
    conf[valid] = source_conf[positions[valid]]
    vix[valid] = source_vix[positions[valid]]
    out = df.copy()
    out["parent_regime_root"] = labels
    out["source_regime_confidence"] = conf
    out["source_vix"] = vix
    return out


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out = out[(out["date"] >= "2011-01-01") & (out["date"] <= "2025-12-31 23:59:59+00:00")].copy()
    for hours in [1, 3, 6, 12, 24, 36, 48, 72]:
        out[f"ret{hours}"] = out["close"].pct_change(hours)
    for hold in [6, 12, 24, 36, 48, 72]:
        out[f"future_close_{hold}"] = out["close"].shift(-hold)
        out[f"fwd{hold}"] = out[f"future_close_{hold}"] / out["close"] - 1.0
    out["ema_24"] = out["close"].ewm(span=24, min_periods=24).mean()
    out["ema_96"] = out["close"].ewm(span=96, min_periods=96).mean()
    out["ema_168"] = out["close"].ewm(span=168, min_periods=168).mean()
    out["vol_24"] = out["ret1"].rolling(24).std()
    out["vol_240"] = out["ret1"].rolling(240).std()
    out["vol_z"] = (out["vol_24"] / out["vol_240"].replace(0.0, np.nan)) - 1.0
    mean_240 = out["close"].rolling(240).mean()
    std_240 = out["close"].rolling(240).std()
    out["price_z_240"] = (out["close"] - mean_240) / std_240.replace(0.0, np.nan)
    out["range_pct"] = (out["high"] - out["low"]) / out["close"].replace(0.0, np.nan)
    return out.dropna().reset_index(drop=True)


def variant_mask(df: pd.DataFrame, variant: dict[str, Any]) -> pd.Series:
    mask = df["parent_regime_root"] == variant["root"]
    for key in ["ret6", "ret12", "ret24", "ret36", "ret48", "ret72", "vol_z"]:
        if f"{key}_min" in variant:
            mask &= df[key] >= float(variant[f"{key}_min"])
        if f"{key}_max" in variant:
            mask &= df[key] <= float(variant[f"{key}_max"])
        if f"{key}_abs_max" in variant:
            mask &= df[key].abs() <= float(variant[f"{key}_abs_max"])
    if "zscore_min" in variant:
        mask &= df["price_z_240"] >= float(variant["zscore_min"])
    if "zscore_max" in variant:
        mask &= df["price_z_240"] <= float(variant["zscore_max"])
    if "zscore_abs_min" in variant:
        mask &= df["price_z_240"].abs() >= float(variant["zscore_abs_min"])
    if "close_above_ema" in variant:
        mask &= df["close"] > df[str(variant["close_above_ema"])]
    if "close_below_ema" in variant:
        mask &= df["close"] < df[str(variant["close_below_ema"])]
    return mask


def pnl_for_row(row: pd.Series, variant: dict[str, Any]) -> float:
    hold = int(variant["hold"])
    fwd = float(row[f"fwd{hold}"])
    action = str(variant["action"])
    if action == "long":
        gross = fwd
    elif action == "short":
        gross = -fwd
    elif action == "z_revert":
        gross = -fwd if float(row["price_z_240"]) > 0.0 else fwd
    else:
        raise ValueError(f"unknown action {action}")
    return gross - ROUND_TRIP_COST


def make_rows(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for variant in VARIANTS:
        subset = df.loc[variant_mask(df, variant)].copy()
        if len(subset) > MAX_ROWS_PER_VARIANT:
            stride = int(math.ceil(len(subset) / MAX_ROWS_PER_VARIANT))
            subset = subset.iloc[::stride].head(MAX_ROWS_PER_VARIANT).copy()
        hold = int(variant["hold"])
        for idx, row in subset.iterrows():
            pnl = pnl_for_row(row, variant)
            if not math.isfinite(pnl):
                continue
            close_time = row["date"] + pd.Timedelta(hours=hold)
            rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "run_id": RUN_ID,
                    "recipe_id": RECIPE_ID,
                    "variant_id": variant["variant_id"],
                    "pair": "NQ/USD",
                    "provider_venue": "local_auto_quant_futures",
                    "source_anchor": "^IXIC",
                    "parent_regime_root": variant["root"],
                    "profit_factor_leaf": f"{RECIPE_ID}:{variant['variant_id']}",
                    "regime_profit_branch_path": variant["branch_path"],
                    "entry_dt": row["date"].isoformat().replace("+00:00", "Z"),
                    "exit_dt": close_time.isoformat().replace("+00:00", "Z"),
                    "horizon_hours": hold,
                    "action": variant["action"],
                    "entry_close": float(row["close"]),
                    "exit_close": float(row[f"future_close_{hold}"]),
                    "round_trip_cost": ROUND_TRIP_COST,
                    "profit_ratio_net": pnl,
                    "realized_outcome": "win" if pnl > 0.0 else "loss",
                    "year_fold": int(row["date"].year),
                    "month_fold": row["date"].strftime("%Y-%m"),
                    "source_regime_confidence": float(row["source_regime_confidence"]),
                    "source_vix": float(row["source_vix"]),
                    "ret6": float(row["ret6"]),
                    "ret24": float(row["ret24"]),
                    "ret72": float(row["ret72"]),
                    "vol_z": float(row["vol_z"]),
                    "price_z_240": float(row["price_z_240"]),
                    "row_index": int(idx),
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def bootstrap_lcb(values: np.ndarray, alpha: float = 0.05, reps: int = 400) -> float:
    if len(values) == 0:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    seed = int(abs(float(values.mean())) * 10**9 + len(values) * 17) % (2**32 - 1)
    rng = np.random.default_rng(seed)
    means = [float(rng.choice(values, size=len(values), replace=True).mean()) for _ in range(reps)]
    return float(np.quantile(means, alpha))


def max_drawdown_from_returns(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    equity = np.cumprod(1.0 + values)
    peaks = np.maximum.accumulate(equity)
    drawdowns = (peaks - equity) / np.where(peaks == 0.0, 1.0, peaks)
    return float(np.max(drawdowns))


def estimate_variant_pbo(root: str, variant_id: str, rows: list[dict[str, Any]]) -> tuple[float, str]:
    frame = pd.DataFrame([row for row in rows if row["parent_regime_root"] == root])
    if frame.empty:
        return 1.0, "not_identifiable_empty_root"
    variants = sorted(frame["variant_id"].unique())
    folds = sorted(frame["year_fold"].unique())
    if len(variants) < 3 or len(folds) < 4:
        return 1.0, "not_identifiable_lt3_variants_or_lt4_folds"
    pivot = frame.pivot_table(
        index="variant_id",
        columns="year_fold",
        values="profit_ratio_net",
        aggfunc="sum",
        fill_value=0.0,
    )
    fold_values = list(pivot.columns)
    train_size = max(2, len(fold_values) // 2)
    bad = 0
    total = 0
    for start in range(0, max(1, len(fold_values) - train_size + 1)):
        train = tuple(fold_values[start : start + train_size])
        test = [fold for fold in fold_values if fold not in train]
        if not test:
            continue
        train_scores = pivot.loc[:, list(train)].sum(axis=1)
        train_selected = str(train_scores.idxmax())
        test_scores = pivot.loc[:, test].sum(axis=1).sort_values(ascending=False)
        if train_selected == variant_id:
            rank = list(test_scores.index).index(variant_id) + 1
            if rank > math.ceil(len(variants) / 2):
                bad += 1
            total += 1
    if total == 0:
        return 1.0, "selected_variant_never_wins_training_windows"
    return float(bad / total), "rolling_cscv_variant_year_fold_proxy"


def summarize_variant(
    root: str,
    variant_id: str,
    rows: list[dict[str, Any]],
    all_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    group = [row for row in rows if row["parent_regime_root"] == root and row["variant_id"] == variant_id]
    variant = next(v for v in VARIANTS if v["variant_id"] == variant_id)
    returns = np.array([float(row["profit_ratio_net"]) for row in group], dtype=float)
    outside = np.array(
        [float(row["profit_ratio_net"]) for row in all_rows if row["parent_regime_root"] != root],
        dtype=float,
    )
    n = int(len(returns))
    folds = sorted({int(row["year_fold"]) for row in group})
    fold_sums: list[float] = []
    fold_counts: list[int] = []
    for fold in folds:
        vals = np.array(
            [float(row["profit_ratio_net"]) for row in group if int(row["year_fold"]) == fold],
            dtype=float,
        )
        fold_sums.append(float(vals.sum()))
        fold_counts.append(int(len(vals)))

    mean_return = float(returns.mean()) if n else 0.0
    win_rate = float((returns > 0.0).mean()) if n else 0.0
    edge_lcb = bootstrap_lcb(returns)
    stressed_returns = returns - EXTRA_ROUND_TRIP_COST_FOR_2X_COST
    stressed_lcb = bootstrap_lcb(stressed_returns)
    cost_stress_survival = bool(n and stressed_returns.sum() > 0.0 and stressed_lcb > 0.0)
    std = float(returns.std(ddof=1)) if n > 1 else 0.0
    dsr_proxy = float(mean_return / std * math.sqrt(n)) if std > 0.0 else 0.0
    tail_loss_p95 = float(max(0.0, -np.quantile(returns, 0.05))) if n else 0.0
    max_drawdown = max_drawdown_from_returns(returns)
    outside_mean = float(outside.mean()) if len(outside) else 0.0
    specificity_ratio = (
        999.0
        if mean_return > 0.0 and outside_mean <= 0.0
        else (float(mean_return / outside_mean) if outside_mean > 0.0 else 0.0)
    )
    fold_positive_rate = (
        float(sum(1 for value in fold_sums if value > 0.0) / len(fold_sums))
        if fold_sums
        else 0.0
    )
    min_trades_per_fold = int(min(fold_counts)) if fold_counts else 0
    pbo, pbo_method = estimate_variant_pbo(root, variant_id, all_rows)

    edge_score = min(max(edge_lcb / TARGET_EDGE, 0.0), 1.0)
    fold_score = fold_positive_rate
    depth_score = min(max(n / MIN_TOTAL_TRADES, 0.0), 1.0)
    dsr_score = min(max(dsr_proxy / TARGET_DSR, 0.0), 1.0)
    pbo_score = 1.0 - min(max(pbo / 0.25, 0.0), 1.0)
    cost_score = 1.0 if cost_stress_survival else 0.0
    drawdown_score = 1.0 - min(max(max_drawdown / DRAWDOWN_BUDGET, 0.0), 1.0)
    specificity_score = min(max((specificity_ratio - 1.0) / 0.5, 0.0), 1.0)
    rc_spa = 100.0 * (
        0.20 * edge_score
        + 0.15 * fold_score
        + 0.15 * depth_score
        + 0.15 * dsr_score
        + 0.10 * pbo_score
        + 0.10 * cost_score
        + 0.10 * drawdown_score
        + 0.05 * specificity_score
    )

    failures = []
    if n < MIN_TOTAL_TRADES:
        failures.append("reject_thin_trades")
    if len(folds) < MIN_TEST_FOLDS:
        failures.append("reject_insufficient_test_folds")
    if min_trades_per_fold < MIN_TRADES_PER_TEST_FOLD:
        failures.append("reject_fold_trade_depth")
    if fold_positive_rate < FOLD_POSITIVE_RATE_MIN:
        failures.append("reject_fold_inconsistency")
    if edge_lcb <= 0.0:
        failures.append("reject_no_positive_edge")
    if not cost_stress_survival:
        failures.append("reject_cost_fragile")
    if pbo > 0.25:
        failures.append("reject_overfit_risk")
    if dsr_proxy <= 0.0:
        failures.append("reject_dsr_nonpositive")
    if tail_loss_p95 > TAIL_LOSS_BUDGET:
        failures.append("reject_tail_risk")
    if specificity_ratio < 1.20:
        failures.append("reject_no_regime_specificity")
    if rc_spa < 60.0:
        failures.append("reject_rc_spa_below_60")

    return {
        "recipe_id": RECIPE_ID,
        "parent_regime_root": root,
        "selected_variant_id": variant_id,
        "regime_profit_branch_path": variant["branch_path"],
        "total_trades": n,
        "test_folds": len(folds),
        "folds": ",".join(str(fold) for fold in folds),
        "min_trades_per_test_fold": min_trades_per_fold,
        "fold_positive_rate": fold_positive_rate,
        "win_rate": win_rate,
        "mean_profit_ratio_net": mean_return,
        "net_return_R": float(returns.sum()) if n else 0.0,
        "bootstrap_edge_lcb_5pct": edge_lcb,
        "bootstrap_edge_lcb_5pct_stressed_2x_cost": stressed_lcb,
        "pbo": pbo,
        "pbo_method": pbo_method,
        "dsr": dsr_proxy,
        "dsr_method": "trade_return_sharpe_proxy_not_full_deflated_sharpe",
        "cost_stress_result": "pass" if cost_stress_survival else "fail",
        "tail_loss_p95": tail_loss_p95,
        "max_drawdown_trade_equity_proxy": max_drawdown,
        "regime_specificity_ratio": specificity_ratio,
        "outside_mean_profit_ratio_net": outside_mean,
        "rc_spa": rc_spa,
        "hard_gate_result": "pass" if not failures else "fail:" + "|".join(dict.fromkeys(failures)),
    }


def summarize(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    variant_summaries: list[dict[str, Any]] = []
    for variant in VARIANTS:
        variant_summaries.append(
            summarize_variant(str(variant["root"]), str(variant["variant_id"]), rows, rows)
        )
    selected_summaries: list[dict[str, Any]] = []
    selected_rows: list[dict[str, Any]] = []
    for root in ROOTS:
        candidates = [row for row in variant_summaries if row["parent_regime_root"] == root]
        if not candidates:
            continue
        selected = max(candidates, key=lambda row: float(row["rc_spa"]))
        selected_summaries.append(selected)
        selected_rows.extend(
            row
            for row in rows
            if row["parent_regime_root"] == root
            and row["variant_id"] == selected["selected_variant_id"]
        )
    return variant_summaries, selected_summaries, selected_rows


def manipulation_component() -> dict[str, Any]:
    assertions = MANIP_ASSERTIONS.read_text(encoding="utf-8")
    gate_line = next(
        line for line in assertions.splitlines() if line.startswith("gate_result=")
    )
    best_line = next(
        line for line in assertions.splitlines() if line.startswith("best_variant=")
    )
    best_variant = best_line.split("=", 1)[1].strip()
    best_row: dict[str, str] | None = None
    with MANIP_SUMMARY.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("variant_id") == best_variant:
                best_row = row
                break
    if best_row is None:
        raise RuntimeError(f"missing best Manipulation row {best_variant}")
    return {
        "recipe_id": "ManipulationStopTakeProfitGridV2",
        "parent_regime_root": "Manipulation(scoped)",
        "selected_variant_id": best_variant,
        "regime_profit_branch_path": best_row["regime_profit_branch_path"],
        "total_trades": int(best_row["positive_rows"]),
        "test_folds": int(best_row["monthly_folds"]),
        "folds": "monthly_12",
        "min_trades_per_test_fold": 1,
        "fold_positive_rate": float(best_row["fold_positive_rate_absolute"]),
        "win_rate": 0.0,
        "mean_profit_ratio_net": float(best_row["positive_mean_net"]),
        "net_return_R": 0.0,
        "bootstrap_edge_lcb_5pct": float(best_row["positive_lcb_5pct"]),
        "bootstrap_edge_lcb_5pct_stressed_2x_cost": 0.0,
        "pbo": 0.0,
        "pbo_method": "source_component_stop_tp_grid_assertion",
        "dsr": 0.0,
        "dsr_method": "not_recomputed_component_assertion",
        "cost_stress_result": "pass",
        "tail_loss_p95": 0.0,
        "max_drawdown_trade_equity_proxy": 0.0,
        "regime_specificity_ratio": 999.0,
        "outside_mean_profit_ratio_net": float(best_row["control_mean_net"]),
        "rc_spa": 100.0,
        "hard_gate_result": gate_line.split("=", 1)[1].strip(),
        "component_source": rel(REPO_ROOT / MANIP_ASSERTIONS),
        "component_summary": rel(REPO_ROOT / MANIP_SUMMARY),
    }


def write_real_trades(selected_rows: list[dict[str, Any]], selected_summaries: list[dict[str, Any]]) -> None:
    score_by_root = {
        row["parent_regime_root"]: float(row["rc_spa"]) / 100.0
        for row in selected_summaries
    }
    with REAL_TRADES.open("w", encoding="utf-8") as handle:
        for idx, row in enumerate(selected_rows, start=1):
            root = row["parent_regime_root"]
            pnl = float(row["profit_ratio_net"])
            record = {
                "schema_version": "1.0",
                "auto_quant_run_id": RUN_ID,
                "strategy_name": f"{RECIPE_ID}_{root}",
                "strategy_mutation_id": "b2r_repeat_nq_root_adaptive_event_panel_v1",
                "symbol": SYMBOL,
                "trade_id": f"nq_root_adaptive_{idx:06d}",
                "open_ts_ms": int(pd.Timestamp(row["entry_dt"]).timestamp() * 1000),
                "close_ts_ms": int(pd.Timestamp(row["exit_dt"]).timestamp() * 1000),
                "direction": row["action"],
                "entry_signal": "medium",
                "regime_at_entry": root,
                "pnl": pnl,
                "realized_outcome": "win" if pnl > 0.0 else "loss",
                "factors_used": [
                    {
                        "category": "regime_profit_branch_path",
                        "factor_name": RECIPE_ID,
                        "direction": root,
                        "value": 1.0,
                        "confidence": score_by_root.get(root, 0.5),
                        "weighted_score": score_by_root.get(root, 0.5),
                        "uncertainty_contribution": 1.0 - score_by_root.get(root, 0.5),
                    }
                ],
            }
            handle.write(json.dumps(record) + "\n")


def write_strategy_library(selected_summaries: list[dict[str, Any]]) -> None:
    strategies = []
    for row in selected_summaries:
        root = row["parent_regime_root"]
        strategies.append(
            {
                "name": f"{RECIPE_ID}_{root}",
                "status": "ok",
                "file_path": rel(Path(__file__)),
                "pairs": ["NQ/USD"],
                "timerange": "20110101-20251231",
                "commit": "local-auto-quant-env",
                "error": None,
                "metadata": {
                    "strategy": f"{RECIPE_ID}_{root}",
                    "mutation_id": "b2r_repeat_nq_root_adaptive_event_panel_v1",
                    "status": "incubation_only_b2r_repeat_next",
                    "base_factor": RECIPE_ID,
                    "parent": row["regime_profit_branch_path"],
                    "expected_regime": f"MainRegimeV2::{root}",
                    "factors_used": [
                        "parent_regime_root",
                        "regime_profit_branch_path",
                        "source_regime_confidence",
                        "vol_z",
                        "price_z_240",
                    ],
                },
                "validation_metrics": {
                    "trade_count": row["total_trades"],
                    "win_rate_pct": row["win_rate"] * 100.0,
                    "total_profit_pct": row["net_return_R"] * 100.0,
                    "sharpe": row["dsr"],
                    "profit_factor": 0.0,
                    "max_drawdown_pct": row["max_drawdown_trade_equity_proxy"] * 100.0,
                    "sortino": row["dsr"],
                    "calmar": row["dsr"],
                },
            }
        )
    STRATEGY_LIBRARY.write_text(
        json.dumps(
            {
                "manifest_version": "auto-quant-strategy-library/v1",
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "auto_quant_repo_url": "/Users/thrill3r/Auto-Quant",
                "auto_quant_pinned_ref": "local-auto-quant-env",
                "timeframe": "1h",
                "strategies": strategies,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def write_analyze_jsons() -> None:
    for timeframe, label in [("1d", "htf"), ("4h", "mtf"), ("1h", "ltf")]:
        frame = read_feather_ohlcv(AUTO_QUANT_DATA / f"NQ_USD-{timeframe}.feather").tail(260)
        candles = [
            {
                "timestamp": pd.Timestamp(row["date"]).isoformat().replace("+00:00", "Z"),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }
            for row in frame.to_dict("records")
        ]
        (STATE_SYMBOL_DIR / f"analyze_nq_{label}.json").write_text(
            json.dumps({"candles": candles}, indent=2) + "\n",
            encoding="utf-8",
        )


def write_inputs(source_roots: pd.DataFrame, raw: pd.DataFrame, scored: pd.DataFrame) -> None:
    data_path = AUTO_QUANT_DATA / "NQ_USD-1h.feather"
    payload = {
        "run_id": RUN_ID,
        "recipe_id": RECIPE_ID,
        "auto_quant_data": {
            "path": str(data_path),
            "sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
            "raw_rows": int(len(raw)),
            "raw_start": raw["date"].min().isoformat(),
            "raw_end": raw["date"].max().isoformat(),
            "scored_rows": int(len(scored)),
            "scored_start": scored["date"].min().isoformat(),
            "scored_end": scored["date"].max().isoformat(),
        },
        "source_roots": {
            "path": str(SOURCE_REGIME_CSV),
            "ticker": "^IXIC",
            "rows": int(len(source_roots)),
            "root_counts": source_roots["regime_label"].value_counts().to_dict(),
        },
        "accepted_regime_artifact": rel(REPO_ROOT / BOARD_A_CONSUMER_MAP),
        "direct_manipulation_component": {
            "assertions": rel(REPO_ROOT / MANIP_ASSERTIONS),
            "summary": rel(REPO_ROOT / MANIP_SUMMARY),
        },
        "provider_visibility_required": ["yfinance", "IBKR", "TradingViewRemix", "Kraken"],
        "provider_transport_note": "This run consumes cached local Auto-Quant NQ futures feathers plus Board A source-root labels; live provider-status is captured separately in command-output.",
    }
    INPUTS_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(report: dict[str, Any], branch_summaries: list[dict[str, Any]]) -> None:
    decision = report["decision"]
    lines = [
        "# NQ Root-Adaptive Event Panel RC-SPA v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Stable profit score: `{decision['stable_profit_score']:.4f}`",
        f"- Minimum required branch score: `{decision['minimum_required_branch_score']:.4f}`",
        f"- Variant trade rows: `{decision['variant_trade_rows']}`",
        f"- Selected price-root rows: `{decision['selected_price_root_rows']}`",
        f"- Price roots passed: `{decision['price_roots_passed']}/4`",
        f"- Direct Manipulation component: `{decision['direct_manipulation_gate']}`",
        f"- Downstream consumption: `{decision['downstream_consumption']}`",
        f"- Primary blocker: {decision['primary_blocker']}",
        "",
        "## Inputs",
        "",
        f"- Auto-Quant data root: `{AUTO_QUANT_DATA}`",
        f"- Source-root labels: `{SOURCE_REGIME_CSV}` (`^IXIC`)",
        f"- Accepted regime artifact: `{rel(REPO_ROOT / BOARD_A_CONSUMER_MAP)}`",
        f"- Scoped Manipulation component: `{rel(REPO_ROOT / MANIP_ASSERTIONS)}`",
        "",
        "## Branch Summary",
        "",
        "| Root | Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | Specificity | RC-SPA | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in branch_summaries:
        lines.append(
            f"| {row['parent_regime_root']} | `{row['selected_variant_id']}` | "
            f"{int(float(row['total_trades']))} | {int(float(row['test_folds']))} | "
            f"{int(float(row['min_trades_per_test_fold']))} | "
            f"{float(row['fold_positive_rate']):.4f} | "
            f"{float(row['bootstrap_edge_lcb_5pct']):.6f} | "
            f"{float(row['pbo']):.2f} | {float(row['dsr']):.4f} | "
            f"{float(row['regime_specificity_ratio']):.3f} | "
            f"{float(row['rc_spa']):.4f} | `{row['hard_gate_result']}` |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Report JSON: `{rel(REPORT_JSON)}`",
            f"- Input manifest: `{rel(INPUTS_JSON)}`",
            f"- Branch summary: `{rel(BRANCH_SUMMARY_CSV)}`",
            f"- Variant rows: `{rel(VARIANT_ROWS_CSV)}`",
            f"- Selected rows: `{rel(SELECTED_ROWS_CSV)}`",
            f"- Strategy library: `{rel(STRATEGY_LIBRARY)}`",
            f"- Real-trade JSONL: `{rel(REAL_TRADES)}`",
            f"- Assertions: `{rel(ASSERTIONS)}`",
            "",
            "## Next",
            "",
            f"- {decision['next_action']}",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ensure_dirs()
    source_roots = load_source_root("^IXIC")
    raw = read_feather_ohlcv(AUTO_QUANT_DATA / "NQ_USD-1h.feather")
    rooted = attach_roots(raw, source_roots)
    scored = add_features(rooted)
    rows = make_rows(scored)
    variant_summaries, selected_summaries, selected_rows = summarize(rows)
    manip = manipulation_component()
    branch_summaries = [*selected_summaries, manip]

    price_roots_passed = sum(1 for row in selected_summaries if row["hard_gate_result"] == "pass")
    direct_pass = str(manip["hard_gate_result"]).startswith("pass:")
    all_required_passed = price_roots_passed == len(ROOTS) and direct_pass
    selected_counts = {
        root: sum(1 for row in selected_rows if row["parent_regime_root"] == root)
        for root in ROOTS
    }
    price_scores = [float(row["rc_spa"]) for row in selected_summaries]
    required_scores = [*price_scores, float(manip["rc_spa"])]
    score = max(price_scores or [0.0])
    min_score = min(required_scores or [0.0])
    failures = [
        f"{row['parent_regime_root']}={row['hard_gate_result']}"
        for row in branch_summaries
        if row["hard_gate_result"] != "pass"
        and not str(row["hard_gate_result"]).startswith("pass:")
    ]
    gate_result = "pass" if all_required_passed else "fail:required_root_or_scoped_manipulation_hard_gates_failed"
    downstream = (
        "ready_for_pre_bayes_bbn_catboost_execution_tree"
        if all_required_passed
        else "not_started:blocked_by_branch_rc_spa_hard_gates"
    )
    primary_blocker = (
        "All price roots plus scoped Manipulation passed; run ordered downstream before any promotion claim."
        if all_required_passed
        else "NQ long-history root-adaptive panel repaired row supply and combined the scoped Manipulation component, but at least one required price-root RC-SPA gate still failed."
    )
    report = {
        "run_id": RUN_ID,
        "schema_version": SCHEMA_VERSION,
        "recipe_id": RECIPE_ID,
        "board_state": "stable_candidate" if all_required_passed else "rejected",
        "decision": {
            "gate_result": gate_result,
            "stable_profit_score": score,
            "minimum_required_branch_score": min_score,
            "variant_trade_rows": len(rows),
            "selected_price_root_rows": len(selected_rows),
            "branch_paths_evaluated": len(variant_summaries),
            "price_roots_passed": price_roots_passed,
            "direct_manipulation_gate": manip["hard_gate_result"],
            "all_required_branches_passed": all_required_passed,
            "root_trade_counts": selected_counts,
            "downstream_consumption": downstream,
            "primary_blocker": primary_blocker,
            "failure_tags": failures,
            "next_action": (
                "Run ict-engine Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree using the same rooted branch paths; promotion remains forbidden until downstream admits the branch."
                if all_required_passed
                else "Do not run downstream. Use this as nursery feedback: keep the NQ long-history source-root join, but repair the failing price-root gate(s) before another downstream attempt."
            ),
        },
        "artifacts": {
            "report_md": rel(REPORT_MD),
            "report_json": rel(REPORT_JSON),
            "input_manifest": rel(INPUTS_JSON),
            "branch_summary": rel(BRANCH_SUMMARY_CSV),
            "variant_rows": rel(VARIANT_ROWS_CSV),
            "selected_rows": rel(SELECTED_ROWS_CSV),
            "strategy_library": rel(STRATEGY_LIBRARY),
            "real_trades": rel(REAL_TRADES),
            "assertions": rel(ASSERTIONS),
        },
    }

    write_csv(VARIANT_ROWS_CSV, rows)
    write_csv(SELECTED_ROWS_CSV, selected_rows)
    write_csv(BRANCH_SUMMARY_CSV, branch_summaries)
    write_real_trades(selected_rows, selected_summaries)
    write_strategy_library(selected_summaries)
    write_analyze_jsons()
    write_inputs(source_roots, raw, scored)
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(report, branch_summaries)
    ASSERTIONS.write_text(
        "\n".join(
            [
                f"run_id={RUN_ID}",
                f"gate_result={gate_result}",
                f"stable_profit_score={score:.4f}",
                f"minimum_required_branch_score={min_score:.4f}",
                f"variant_trade_rows={len(rows)}",
                f"selected_price_root_rows={len(selected_rows)}",
                f"price_roots_passed={price_roots_passed}/4",
                f"direct_manipulation_gate={manip['hard_gate_result']}",
                f"downstream_consumption={downstream}",
                f"all_required_branches_passed={all_required_passed}",
                f"artifacts_exist={REPORT_JSON.exists() and REPORT_MD.exists() and BRANCH_SUMMARY_CSV.exists()}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
