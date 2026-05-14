#!/usr/bin/env python3
"""Board B B2R-repeat-next volatility/carry provider-panel readback.

This is an additive Auto-Quant-side experiment. It reads local Auto-Quant
provider data, attaches Board A root labels, scores a materially different
volatility/liquidity/carry family, and preserves the existing scoped
Manipulation component as a separate branch.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260512T024349+0800-codex-board-b-b2r-repeat-next-vol-carry-provider-panel-v1"
SCHEMA_VERSION = "board-b-b2r-repeat-next-vol-carry-provider-panel/v1"
RECIPE_ID = "RootLiquidityVolCarryRotationV1"
ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
SELECTED_VARIANT_ID = "balanced_vol_carry"

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
MANIP_SUMMARY = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T194231-codex-board-b-root-plus-manip-bridge-rc-spa-v1/branch-rc-spa/"
    "root_plus_manip_bridge_branch_summary_v1.csv"
)

PANEL = [
    {"pair": "NQ/USD", "file": "NQ_USD-1h.feather", "source": "^IXIC", "venue": "local_auto_quant_futures"},
    {"pair": "QQQ/USD", "file": "QQQ_USD-1h.feather", "source": "^IXIC", "venue": "local_auto_quant_yfinance"},
    {"pair": "SPY/USD", "file": "SPY_USD-1h.feather", "source": "^GSPC", "venue": "local_auto_quant_yfinance"},
    {"pair": "IWM/USD", "file": "IWM_USD-1h.feather", "source": "^RUT", "venue": "local_auto_quant_yfinance"},
    {"pair": "DIA/USD", "file": "DIA_USD-1h.feather", "source": "^GSPC", "venue": "local_auto_quant_yfinance"},
    {"pair": "GLD/USD", "file": "GLD_USD-1h.feather", "source": "^GSPC", "venue": "local_auto_quant_yfinance"},
    {"pair": "BTC/USDT", "file": "BTC_USDT-1h.feather", "source": "^IXIC", "venue": "local_auto_quant_crypto"},
    {"pair": "ETH/USDT", "file": "ETH_USDT-1h.feather", "source": "^IXIC", "venue": "local_auto_quant_crypto"},
    {"pair": "SOL/USDT", "file": "SOL_USDT-1h.feather", "source": "^IXIC", "venue": "local_auto_quant_crypto"},
    {"pair": "BNB/USDT", "file": "BNB_USDT-1h.feather", "source": "^IXIC", "venue": "local_auto_quant_crypto"},
    {"pair": "AVAX/USDT", "file": "AVAX_USDT-1h.feather", "source": "^IXIC", "venue": "local_auto_quant_crypto"},
]

VARIANTS = [
    {
        "variant_id": "balanced_vol_carry",
        "horizon": 12,
        "bull_mom": 0.0025,
        "bear_mom": -0.0035,
        "sideways_pullback": -0.0045,
        "sideways_band": 0.018,
        "crisis_shock": -0.0065,
        "crisis_vol_z": 0.40,
        "max_vol_z": 2.00,
    },
    {
        "variant_id": "faster_liquidity_revert",
        "horizon": 6,
        "bull_mom": 0.0015,
        "bear_mom": -0.0025,
        "sideways_pullback": -0.0030,
        "sideways_band": 0.014,
        "crisis_shock": -0.0050,
        "crisis_vol_z": 0.25,
        "max_vol_z": 2.50,
    },
    {
        "variant_id": "slow_carry_rotation",
        "horizon": 24,
        "bull_mom": 0.0040,
        "bear_mom": -0.0060,
        "sideways_pullback": -0.0075,
        "sideways_band": 0.026,
        "crisis_shock": -0.0100,
        "crisis_vol_z": 0.65,
        "max_vol_z": 1.60,
    },
    {
        "variant_id": "defensive_short_bias",
        "horizon": 10,
        "bull_mom": 0.0030,
        "bear_mom": -0.0020,
        "sideways_pullback": -0.0060,
        "sideways_band": 0.021,
        "crisis_shock": -0.0040,
        "crisis_vol_z": 0.15,
        "max_vol_z": 3.00,
    },
    {
        "variant_id": "crypto_beta_guarded",
        "horizon": 18,
        "bull_mom": 0.0060,
        "bear_mom": -0.0080,
        "sideways_pullback": -0.0090,
        "sideways_band": 0.035,
        "crisis_shock": -0.0120,
        "crisis_vol_z": 0.55,
        "max_vol_z": 1.80,
    },
]

TARGET_EDGE = 0.001
TARGET_DSR = 1.0
DRAWDOWN_BUDGET = 0.30
TAIL_LOSS_BUDGET = 0.08
MIN_TOTAL_TRADES = 50
MIN_TEST_FOLDS = 4
MIN_TRADES_PER_TEST_FOLD = 3
FOLD_POSITIVE_RATE_MIN = 0.70
ROUND_TRIP_COST = {"local_auto_quant_crypto": 0.0015}
DEFAULT_ROUND_TRIP_COST = 0.0009
EXTRA_ROUND_TRIP_COST_FOR_2X_COST = 0.001
MAX_ROWS_PER_ROOT_VARIANT = 6000


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot find repo root from {start}")


RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = find_repo_root(Path(__file__).resolve())
OUT_DIR = RUN_ROOT / "vol-carry-provider-panel"
CHECK_DIR = RUN_ROOT / "checks"
COMMAND_DIR = RUN_ROOT / "command-output"
REPORT_JSON = OUT_DIR / "vol_carry_provider_panel_rc_spa_v1.json"
REPORT_MD = OUT_DIR / "vol_carry_provider_panel_rc_spa_v1.md"
SELECTED_ROWS_CSV = OUT_DIR / "vol_carry_provider_panel_selected_rows_v1.csv"
VARIANT_ROWS_CSV = OUT_DIR / "vol_carry_provider_panel_variant_rows_v1.csv"
BRANCH_SUMMARY_CSV = OUT_DIR / "vol_carry_provider_panel_branch_summary_v1.csv"
PANEL_JSON = OUT_DIR / "vol_carry_provider_panel_inputs_v1.json"
ASSERTIONS = CHECK_DIR / "vol_carry_provider_panel_v1_assertions.out"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def normalize_date(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_datetime(series, unit="ms", utc=True)
    return pd.to_datetime(series, utc=True)


def load_source_roots() -> dict[str, pd.DataFrame]:
    df = pd.read_csv(
        SOURCE_REGIME_CSV,
        usecols=["date", "ticker", "regime_label", "regime_confidence", "vix"],
    )
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.normalize()
    roots: dict[str, pd.DataFrame] = {}
    for ticker, group in df.groupby("ticker"):
        roots[str(ticker)] = group.sort_values("date").reset_index(drop=True)
    return roots


def attach_roots(df: pd.DataFrame, source_rows: pd.DataFrame) -> pd.DataFrame:
    source_dates = source_rows["date"].to_numpy(dtype="datetime64[ns]")
    source_roots = source_rows["regime_label"].astype(str).to_numpy()
    source_conf = source_rows["regime_confidence"].astype(float).to_numpy()
    source_vix = source_rows["vix"].astype(float).to_numpy()
    bar_dates = df["date"].dt.normalize().to_numpy(dtype="datetime64[ns]")
    positions = np.searchsorted(source_dates, bar_dates, side="right") - 1
    labels = np.full(len(df), "Unlabeled", dtype=object)
    conf = np.full(len(df), np.nan, dtype=float)
    vix = np.full(len(df), np.nan, dtype=float)
    valid = positions >= 0
    labels[valid] = source_roots[positions[valid]]
    conf[valid] = source_conf[positions[valid]]
    vix[valid] = source_vix[positions[valid]]
    df["parent_regime_root"] = labels
    df["source_regime_confidence"] = conf
    df["source_vix"] = vix
    return df


def load_panel(source_roots: dict[str, pd.DataFrame]) -> tuple[list[pd.DataFrame], list[dict[str, Any]]]:
    frames: list[pd.DataFrame] = []
    inputs: list[dict[str, Any]] = []
    for item in PANEL:
        path = AUTO_QUANT_DATA / item["file"]
        if not path.exists():
            inputs.append({**item, "status": "missing", "path": str(path)})
            continue
        df = pd.read_feather(path)
        df["date"] = normalize_date(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        df = df[(df["date"] >= "2021-01-01") & (df["date"] <= "2026-01-31")].copy()
        df = df.reset_index(drop=True)
        source = source_roots[item["source"]]
        df = attach_roots(df, source)
        df["pair"] = item["pair"]
        df["source_anchor"] = item["source"]
        df["provider_venue"] = item["venue"]
        df["ret_1h"] = df["close"].pct_change()
        df["ret_6h"] = df["close"].pct_change(6)
        df["ret_24h"] = df["close"].pct_change(24)
        df["ret_72h"] = df["close"].pct_change(72)
        df["ema_24"] = df["close"].ewm(span=24, min_periods=24).mean()
        df["ema_96"] = df["close"].ewm(span=96, min_periods=96).mean()
        df["vol_24h"] = df["ret_1h"].rolling(24).std()
        df["vol_168h"] = df["ret_1h"].rolling(168).std()
        df["vol_z"] = (df["vol_24h"] / df["vol_168h"].replace(0.0, np.nan)) - 1.0
        df["range_pct"] = (df["high"] - df["low"]) / df["close"].replace(0.0, np.nan)
        df["future_close_6"] = df["close"].shift(-6)
        df["future_close_10"] = df["close"].shift(-10)
        df["future_close_12"] = df["close"].shift(-12)
        df["future_close_18"] = df["close"].shift(-18)
        df["future_close_24"] = df["close"].shift(-24)
        frames.append(df)
        inputs.append(
            {
                **item,
                "status": "loaded",
                "path": str(path),
                "rows": int(len(df)),
                "start": df["date"].min().isoformat() if len(df) else None,
                "end": df["date"].max().isoformat() if len(df) else None,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return frames, inputs


def branch_path_for_root(root: str, variant_id: str) -> str:
    paths = {
        "Bull": f"Bull -> TrendExpansion -> LiquidityVolCarryContinuation -> {RECIPE_ID}:{variant_id}",
        "Bear": f"Bear -> BearMarketDrawdown -> DefensiveVolCarryShort -> {RECIPE_ID}:{variant_id}",
        "Sideways": f"Sideways -> RangeConsolidation -> LiquidityMeanReversionCarry -> {RECIPE_ID}:{variant_id}",
        "Crisis": f"Crisis -> ExtremeStress -> VolatilityShockShort -> {RECIPE_ID}:{variant_id}",
        "Manipulation(scoped)": "Manipulation(scoped) -> TelegramPumpEvent -> SourceBuyBinanceIntradayExit -> pnl_bridge",
    }
    return paths.get(root, f"{root} -> Unknown -> {RECIPE_ID}:{variant_id}")


def signal_rows(frames: list[pd.DataFrame], variant: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    horizon = int(variant["horizon"])
    future_col = f"future_close_{horizon}"
    for df in frames:
        if future_col not in df:
            continue
        common = (
            df["parent_regime_root"].isin(ROOTS)
            & df[future_col].notna()
            & df["ret_24h"].notna()
            & df["ret_6h"].notna()
            & df["ret_72h"].notna()
            & df["vol_z"].notna()
            & (df["vol_z"] < float(variant["max_vol_z"]))
        )
        bull = (
            common
            & (df["parent_regime_root"] == "Bull")
            & (df["ret_24h"] > float(variant["bull_mom"]))
            & (df["close"] > df["ema_96"])
        )
        bear = (
            common
            & (df["parent_regime_root"] == "Bear")
            & (df["ret_24h"] < float(variant["bear_mom"]))
            & (df["close"] < df["ema_96"])
        )
        sideways = (
            common
            & (df["parent_regime_root"] == "Sideways")
            & (df["ret_6h"] < float(variant["sideways_pullback"]))
            & (df["ret_72h"].abs() < float(variant["sideways_band"]))
        )
        crisis = (
            common
            & (df["parent_regime_root"] == "Crisis")
            & (df["ret_6h"] < float(variant["crisis_shock"]))
            & (df["vol_z"] > float(variant["crisis_vol_z"]))
        )
        masks = [
            ("Bull", "long", 1.0, bull),
            ("Bear", "short", -1.0, bear),
            ("Sideways", "long", 1.0, sideways),
            ("Crisis", "short", -1.0, crisis),
        ]
        for root, action, side, mask in masks:
            sub = df.loc[mask].copy()
            if sub.empty:
                continue
            if len(sub) > MAX_ROWS_PER_ROOT_VARIANT:
                stride = int(math.ceil(len(sub) / MAX_ROWS_PER_ROOT_VARIANT))
                sub = sub.iloc[::stride].head(MAX_ROWS_PER_ROOT_VARIANT).copy()
            cost = ROUND_TRIP_COST.get(str(sub["provider_venue"].iloc[0]), DEFAULT_ROUND_TRIP_COST)
            sub["profit_ratio_net"] = side * (sub[future_col] / sub["close"] - 1.0) - cost
            for row in sub.itertuples(index=True):
                profit = float(row.profit_ratio_net)
                if not math.isfinite(profit):
                    continue
                exit_idx = int(row.Index) + horizon
                rows.append(
                    {
                        "run_id": RUN_ID,
                        "recipe_id": RECIPE_ID,
                        "variant_id": str(variant["variant_id"]),
                        "pair": row.pair,
                        "provider_venue": row.provider_venue,
                        "source_anchor": row.source_anchor,
                        "parent_regime_root": root,
                        "profit_factor_leaf": f"{RECIPE_ID}:{variant['variant_id']}",
                        "action": action,
                        "side": int(side),
                        "entry_dt": row.date.isoformat(),
                        "exit_dt": df.loc[exit_idx, "date"].isoformat() if exit_idx < len(df) else "",
                        "entry_close": float(row.close),
                        "exit_close": float(getattr(row, future_col)),
                        "horizon_hours": horizon,
                        "round_trip_cost": cost,
                        "profit_ratio_net": profit,
                        "year_fold": int(row.date.year),
                        "month_fold": row.date.strftime("%Y-%m"),
                        "source_regime_confidence": float(row.source_regime_confidence),
                        "source_vix": float(row.source_vix),
                        "regime_profit_branch_path": branch_path_for_root(root, str(variant["variant_id"])),
                    }
                )
    return rows


def bootstrap_lcb(values: np.ndarray, alpha: float = 0.05, reps: int = 400) -> float:
    if len(values) == 0:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    seed = int(abs(float(values.mean())) * 10**9) % (2**32 - 1)
    rng = np.random.default_rng(seed)
    means = [float(rng.choice(values, size=len(values), replace=True).mean()) for _ in range(reps)]
    return float(np.quantile(means, alpha))


def max_drawdown_from_returns(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    equity = np.cumprod(1.0 + values)
    peaks = np.maximum.accumulate(equity)
    dd = (peaks - equity) / np.where(peaks == 0.0, 1.0, peaks)
    return float(np.max(dd))


def estimate_pbo(root: str, variant_rows: list[dict[str, Any]]) -> tuple[float, str]:
    df = pd.DataFrame([row for row in variant_rows if row["parent_regime_root"] == root])
    if df.empty:
        return 1.0, "not_identifiable_empty_root"
    variants = sorted(df["variant_id"].unique())
    folds = sorted(df["year_fold"].unique())
    if len(variants) < 3 or len(folds) < 4:
        return 1.0, "not_identifiable_lt3_variants_or_lt4_folds"
    pivot = df.pivot_table(
        index="variant_id",
        columns="year_fold",
        values="profit_ratio_net",
        aggfunc="sum",
        fill_value=0.0,
    )
    fold_values = list(pivot.columns)
    train_size = max(2, len(fold_values) // 2)
    combos: list[tuple[Any, ...]] = []
    for i in range(0, max(1, len(fold_values) - train_size + 1)):
        combos.append(tuple(fold_values[i : i + train_size]))
    bad = 0
    total = 0
    for train in combos:
        test = [fold for fold in fold_values if fold not in train]
        if not test:
            continue
        train_scores = pivot.loc[:, list(train)].sum(axis=1)
        selected = str(train_scores.idxmax())
        test_scores = pivot.loc[:, test].sum(axis=1).sort_values(ascending=False)
        rank = list(test_scores.index).index(selected) + 1
        if rank > math.ceil(len(variants) / 2):
            bad += 1
        total += 1
    return (float(bad / total) if total else 1.0, "rolling_cscv_variant_year_fold_proxy")


def summarize_root(
    root: str,
    selected_rows: list[dict[str, Any]],
    variant_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    rows = [row for row in selected_rows if row["parent_regime_root"] == root]
    returns = np.array([float(row["profit_ratio_net"]) for row in rows], dtype=float)
    outside = np.array(
        [float(row["profit_ratio_net"]) for row in selected_rows if row["parent_regime_root"] != root],
        dtype=float,
    )
    n = int(len(returns))
    folds = sorted({int(row["year_fold"]) for row in rows})
    fold_sums: list[float] = []
    fold_counts: list[int] = []
    for fold in folds:
        vals = np.array(
            [float(row["profit_ratio_net"]) for row in rows if int(row["year_fold"]) == fold],
            dtype=float,
        )
        fold_sums.append(float(vals.sum()))
        fold_counts.append(int(len(vals)))

    mean_return = float(returns.mean()) if n else 0.0
    win_rate = float((returns > 0).mean()) if n else 0.0
    bootstrap_edge_lcb = bootstrap_lcb(returns)
    stressed_returns = returns - EXTRA_ROUND_TRIP_COST_FOR_2X_COST
    stressed_lcb = bootstrap_lcb(stressed_returns)
    cost_stress_survival = bool(n and stressed_returns.sum() > 0.0 and stressed_lcb > 0.0)
    std = float(returns.std(ddof=1)) if n > 1 else 0.0
    dsr_proxy = float(mean_return / std * math.sqrt(n)) if std > 0.0 else 0.0
    tail_loss_p95 = float(max(0.0, -np.quantile(returns, 0.05))) if n else 0.0
    mdd = max_drawdown_from_returns(returns)
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
    pbo, pbo_method = estimate_pbo(root, variant_rows)

    edge_score = min(max(bootstrap_edge_lcb / TARGET_EDGE, 0.0), 1.0)
    fold_score = fold_positive_rate
    depth_score = min(max(n / MIN_TOTAL_TRADES, 0.0), 1.0)
    dsr_score = min(max(dsr_proxy / TARGET_DSR, 0.0), 1.0)
    pbo_score = 1.0 - min(max(pbo / 0.25, 0.0), 1.0)
    cost_score = 1.0 if cost_stress_survival else 0.0
    drawdown_score = 1.0 - min(max(mdd / DRAWDOWN_BUDGET, 0.0), 1.0)
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
    if bootstrap_edge_lcb <= 0.0:
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
        "selected_variant_id": SELECTED_VARIANT_ID,
        "regime_profit_branch_path": branch_path_for_root(root, SELECTED_VARIANT_ID),
        "total_trades": n,
        "test_folds": len(folds),
        "folds": ",".join(str(fold) for fold in folds),
        "min_trades_per_test_fold": min_trades_per_fold,
        "fold_positive_rate": fold_positive_rate,
        "win_rate": win_rate,
        "mean_profit_ratio_net": mean_return,
        "net_return_R": float(returns.sum()) if n else 0.0,
        "bootstrap_edge_lcb_5pct": bootstrap_edge_lcb,
        "bootstrap_edge_lcb_5pct_stressed_2x_cost": stressed_lcb,
        "pbo": pbo,
        "pbo_method": pbo_method,
        "dsr": dsr_proxy,
        "dsr_method": "trade_return_sharpe_proxy_not_full_deflated_sharpe",
        "cost_stress_result": "pass" if cost_stress_survival else "fail",
        "tail_loss_p95": tail_loss_p95,
        "max_drawdown_trade_equity_proxy": mdd,
        "regime_specificity_ratio": specificity_ratio,
        "outside_mean_profit_ratio_net": outside_mean,
        "rc_spa": rc_spa,
        "promotion_level": "reject" if failures else ("research_watch" if rc_spa < 75.0 else "stable_candidate"),
        "hard_gate_result": "pass" if not failures else "fail:" + "|".join(dict.fromkeys(failures)),
        "downstream_consumption_status": (
            "not_started:blocked_by_branch_rc_spa_hard_gates"
            if failures
            else "eligible_for_branch_specific_pre_bayes_bbn_catboost_execution_tree_probe"
        ),
    }


def load_manipulation_component() -> dict[str, Any]:
    with MANIP_SUMMARY.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("parent_regime_root") == "Manipulation(scoped)":
                out: dict[str, Any] = dict(row)
                out["recipe_id"] = f"{RECIPE_ID}+ExistingScopedManipulationComponent"
                out["selected_variant_id"] = "existing_mehrnoom_binance_intraday_pnl_bridge"
                out["component_source"] = rel(MANIP_SUMMARY)
                return out
    raise RuntimeError("missing Manipulation(scoped) component row")


def write_report(report: dict[str, Any], branch_summaries: list[dict[str, Any]]) -> None:
    decision = report["decision"]
    lines = [
        "# B2R Repeat Next Vol/Carry Provider Panel v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Stable profit score: `{decision['stable_profit_score']:.4f}`",
        f"- Selected trade rows: `{decision['selected_trade_rows']}`",
        f"- Variant trade rows: `{decision['variant_trade_rows']}`",
        f"- Branch paths evaluated: `{decision['branch_paths_evaluated']}`",
        f"- Branch paths passed: `{decision['branch_paths_passed']}`",
        f"- Root trade counts: `{decision['root_trade_counts']}`",
        f"- Downstream consumption: `{decision['downstream_consumption']}`",
        f"- Primary blocker: {decision['primary_blocker']}",
        "",
        "## Inputs",
        "",
        f"- Auto-Quant data root: `{AUTO_QUANT_DATA}`",
        f"- Board A source roots: `{SOURCE_REGIME_CSV}`",
        f"- Accepted regime artifact: `{rel(REPO_ROOT / BOARD_A_CONSUMER_MAP)}`",
        f"- Existing scoped Manipulation component: `{rel(REPO_ROOT / MANIP_SUMMARY)}`",
        "",
        "## Branch Summary",
        "",
        "| Root | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | Specificity | RC-SPA | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in branch_summaries:
        lines.append(
            f"| {row['parent_regime_root']} | {int(float(row['total_trades']))} | "
            f"{int(float(row['test_folds']))} | {int(float(row['min_trades_per_test_fold']))} | "
            f"{float(row['fold_positive_rate']):.4f} | {float(row['bootstrap_edge_lcb_5pct']):.6f} | "
            f"{float(row['pbo']):.2f} | {float(row['dsr']):.4f} | "
            f"{float(row['regime_specificity_ratio']):.3f} | {float(row['rc_spa']):.4f} | "
            f"`{row['hard_gate_result']}` |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Report JSON: `{rel(REPORT_JSON)}`",
            f"- Provider panel inputs: `{rel(PANEL_JSON)}`",
            f"- Selected rows: `{rel(SELECTED_ROWS_CSV)}`",
            f"- Variant rows: `{rel(VARIANT_ROWS_CSV)}`",
            f"- Branch summary: `{rel(BRANCH_SUMMARY_CSV)}`",
            f"- Assertions: `{rel(ASSERTIONS)}`",
            "",
            "## Next",
            "",
            f"- {decision['next_action']}",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    for path in [OUT_DIR, CHECK_DIR, COMMAND_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    for required in [SOURCE_REGIME_CSV, REPO_ROOT / BOARD_A_CONSUMER_MAP, REPO_ROOT / MANIP_SUMMARY]:
        if not required.exists():
            raise FileNotFoundError(required)

    source_roots = load_source_roots()
    frames, provider_inputs = load_panel(source_roots)
    if not frames:
        raise RuntimeError("no provider panel frames loaded")

    variant_rows: list[dict[str, Any]] = []
    selected_rows: list[dict[str, Any]] = []
    for variant in VARIANTS:
        rows = signal_rows(frames, variant)
        variant_rows.extend(rows)
        if variant["variant_id"] == SELECTED_VARIANT_ID:
            selected_rows = rows

    write_csv(SELECTED_ROWS_CSV, selected_rows)
    write_csv(VARIANT_ROWS_CSV, variant_rows)

    branch_summaries = [summarize_root(root, selected_rows, variant_rows) for root in ROOTS]
    manipulation = load_manipulation_component()
    branch_summaries.append(manipulation)
    write_csv(BRANCH_SUMMARY_CSV, branch_summaries)

    passed = [row for row in branch_summaries if row["hard_gate_result"] == "pass"]
    root_counts = {row["parent_regime_root"]: int(float(row["total_trades"])) for row in branch_summaries}
    score = max(float(row["rc_spa"]) for row in branch_summaries)
    gate_result = "pass" if len(passed) == len(branch_summaries) else "fail:required_root_branch_hard_gates_failed"
    downstream = (
        "eligible_for_pre_bayes_bbn_catboost_execution_tree"
        if gate_result == "pass"
        else "not_started:blocked_by_branch_rc_spa_hard_gates"
    )
    primary_blocker = (
        "B2R-repeat-next used a materially different local Auto-Quant provider panel "
        "and volatility/liquidity/carry family, but required root branches still fail "
        "RC-SPA hard gates; downstream promotion remains blocked."
    )
    decision = {
        "board_state": "stable_candidate" if gate_result == "pass" else "rejected",
        "gate_result": gate_result,
        "stable_profit_score": score,
        "selected_trade_rows": len(selected_rows),
        "variant_trade_rows": len(variant_rows),
        "branch_paths_evaluated": len(branch_summaries),
        "branch_paths_passed": len(passed),
        "root_trade_counts": root_counts,
        "downstream_consumption": downstream,
        "primary_blocker": primary_blocker,
        "next_action": (
            "Do not promote downstream from this vol/carry panel. Use the failure tags to "
            "seed a new B2R nursery branch with stronger Sideways/Crisis edge or source-owned "
            "Manipulation PnL; only run Pre-Bayes/BBN/CatBoost/execution-tree after all required "
            "root branches pass RC-SPA."
        ),
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "recipe_id": RECIPE_ID,
        "selected_variant_id": SELECTED_VARIANT_ID,
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "accepted_regime_artifact": rel(REPO_ROOT / BOARD_A_CONSUMER_MAP),
        "provider_inputs": provider_inputs,
        "variant_definitions": VARIANTS,
        "decision": decision,
        "branch_summaries": branch_summaries,
        "artifacts": {
            "report_json": rel(REPORT_JSON),
            "report_md": rel(REPORT_MD),
            "provider_panel_inputs": rel(PANEL_JSON),
            "selected_rows_csv": rel(SELECTED_ROWS_CSV),
            "variant_rows_csv": rel(VARIANT_ROWS_CSV),
            "branch_summary_csv": rel(BRANCH_SUMMARY_CSV),
            "assertions": rel(ASSERTIONS),
        },
        "completion": {
            "runtime_code_changed": False,
            "auto_quant_checkout_changed": False,
            "raw_auto_quant_data_committed": False,
            "thresholds_relaxed_after_scoring": False,
            "existing_scoped_manipulation_component_reused": True,
            "downstream_runtime_consumed_branch_path": gate_result == "pass",
        },
    }

    write_json(PANEL_JSON, {"panel": provider_inputs, "source_roots": sorted({item["source"] for item in PANEL})})
    write_json(REPORT_JSON, report)
    write_report(report, branch_summaries)

    missing_roots = [root for root in ROOTS if root_counts.get(root, 0) == 0]
    assertions = [
        f"run_id={RUN_ID}",
        f"recipe_id={RECIPE_ID}",
        f"selected_variant_id={SELECTED_VARIANT_ID}",
        f"selected_trade_rows={len(selected_rows)}",
        f"variant_trade_rows={len(variant_rows)}",
        f"root_counts={root_counts}",
        f"branch_paths_evaluated={len(branch_summaries)}",
        f"branch_paths_passed={len(passed)}",
        f"gate_result={gate_result}",
        f"downstream_consumption={downstream}",
        f"report_json={rel(REPORT_JSON)}",
        f"report_md={rel(REPORT_MD)}",
    ]
    if missing_roots:
        assertions.append(f"candidate_failure_missing_required_roots={missing_roots}")
    if len(selected_rows) == 0:
        assertions.append("ASSERT_FAIL selected_trade_rows_zero")
    ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
