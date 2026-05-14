#!/usr/bin/env python3
"""Board B VRP root-branch RC-SPA readback.

This run is intentionally additive and run-local. It consumes existing local
Auto-Quant market feathers plus QQQ/VIX/VIX3M/VVIX sidecars, attaches the
accepted Board A MainRegimeV2 root context by source-date lookup, and scores a
VRP/volatility-compression variant panel with the board's RC-SPA hard gates.
"""

from __future__ import annotations

import csv
import itertools
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260511T190356+0800-codex-board-b-vrp-v25-root-branch-rc-spa-v1"
SCHEMA_VERSION = "board-b-vrp-v25-root-branch-rc-spa/v1"
RECIPE_ID = "VRPCompressionV25RootBranch"
SOURCE_TICKER = "^IXIC"
ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
REQUIRED_PATHS = ["Bull", "Bear", "Sideways", "Crisis", "Manipulation(scoped)"]

DATA_DIR = Path("/Users/thrill3r/Auto-Quant/user_data/data")
PROBE_DIR = Path("/tmp/ict-engine-ibkr-probe")
SOURCE_REGIME_CSV = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)

QQQ_IV_CSV = PROBE_DIR / "qqq.iv.1d.10y.csv"
QQQ_HV_CSV = PROBE_DIR / "qqq.hv.1d.10y.csv"
VVIX_CSV = PROBE_DIR / "vvix.1d.10y.csv"
VIX_CSV = PROBE_DIR / "vix.1d.10y.csv"
VIX3M_CSV = PROBE_DIR / "vix3m.1d.10y.csv"

START = pd.Timestamp("2018-01-01", tz="UTC")
END = pd.Timestamp("2025-12-31", tz="UTC")
TRADING_DAYS = 252.0

STOPLOSS = -0.022
TRAILING_OFFSET = 0.010
TRAILING_STOP = 0.005
EXTRA_ROUND_TRIP_COST_FOR_2X_FEE = 0.002
TARGET_EDGE = 0.005
TARGET_DSR = 1.0
DRAWDOWN_BUDGET = 0.25
TAIL_LOSS_BUDGET = 0.25
MIN_TOTAL_TRADES = 100
MIN_TEST_FOLDS = 4
MIN_TRADES_PER_TEST_FOLD = 10
FOLD_POSITIVE_RATE_MIN = 0.75

PANELS = [
    ("NQ/USD", "5m", DATA_DIR / "NQ_USD-5m.feather", START, END),
    ("NQ/USD", "15m", DATA_DIR / "NQ_USD-15m.feather", START, END),
    ("NQ/USD", "1h", DATA_DIR / "NQ_USD-1h.feather", START, END),
    ("SPY/USD", "15m", DATA_DIR / "SPY_USD-15m.feather", pd.Timestamp("2025-01-01", tz="UTC"), END),
    ("IWM/USD", "15m", DATA_DIR / "IWM_USD-15m.feather", pd.Timestamp("2025-01-01", tz="UTC"), END),
    ("DIA/USD", "15m", DATA_DIR / "DIA_USD-15m.feather", pd.Timestamp("2025-01-01", tz="UTC"), END),
    ("GLD/USD", "15m", DATA_DIR / "GLD_USD-15m.feather", pd.Timestamp("2025-01-01", tz="UTC"), END),
]

VARIANTS: list[dict[str, Any]] = [
    {
        "variant_id": "v2_baseline",
        "iv_lt": 0.30,
        "hv_lt": 0.30,
        "vvix_lt": 0.40,
        "start_hour": 13,
        "end_hour": 21,
        "require_body_green": True,
        "require_long_or_local_trend": True,
    },
    {
        "variant_id": "v25_strict_compression",
        "iv_lt": 0.25,
        "hv_lt": 0.25,
        "vvix_lt": 0.35,
        "start_hour": 13,
        "end_hour": 20,
        "require_body_green": True,
        "require_long_or_local_trend": True,
    },
    {
        "variant_id": "v25_low_vvix",
        "iv_lt": 0.30,
        "hv_lt": 0.30,
        "vvix_lt": 0.32,
        "start_hour": 13,
        "end_hour": 21,
        "require_body_green": True,
        "require_long_or_local_trend": True,
    },
    {
        "variant_id": "v25_no_body_filter",
        "iv_lt": 0.30,
        "hv_lt": 0.30,
        "vvix_lt": 0.40,
        "start_hour": 13,
        "end_hour": 21,
        "require_body_green": False,
        "require_long_or_local_trend": True,
    },
    {
        "variant_id": "v25_rth_tight",
        "iv_lt": 0.30,
        "hv_lt": 0.30,
        "vvix_lt": 0.40,
        "start_hour": 14,
        "end_hour": 20,
        "require_body_green": True,
        "require_long_or_local_trend": True,
    },
    {
        "variant_id": "v25_local_trend_only",
        "iv_lt": 0.32,
        "hv_lt": 0.32,
        "vvix_lt": 0.45,
        "start_hour": 13,
        "end_hour": 21,
        "require_body_green": True,
        "require_long_or_local_trend": False,
    },
]


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot find repo root from {start}")


RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = find_repo_root(Path(__file__).resolve())
BOARD_A_CONSUMER_MAP = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/"
    "regime_factor_consumer_map_v1.csv"
)

OUT_DIR = RUN_ROOT / "branch-rc-spa"
CHECK_DIR = RUN_ROOT / "checks"
FAIL_CLOSED_DIR = RUN_ROOT / "ict-engine-fail-closed"

ALL_ROWS_CSV = OUT_DIR / "vrp_v25_all_variant_branch_rows_v1.csv"
SELECTED_ROWS_CSV = OUT_DIR / "vrp_v25_selected_branch_rows_v1.csv"
SUMMARY_CSV = OUT_DIR / "vrp_v25_branch_rc_spa_summary_v1.csv"
PANEL_SUMMARY_CSV = OUT_DIR / "vrp_v25_panel_variant_summary_v1.csv"
REPORT_JSON = OUT_DIR / "vrp_v25_root_branch_rc_spa_report_v1.json"
REPORT_MD = OUT_DIR / "vrp_v25_root_branch_rc_spa_report_v1.md"
ASSERTIONS = CHECK_DIR / "vrp_v25_root_branch_rc_spa_v1_assertions.out"
FAIL_CLOSED_MD = FAIL_CLOSED_DIR / "vrp_v25_ict_engine_fail_closed_summary_v1.md"


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def to_jsonable(value: Any) -> Any:
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return value.item()
    return value


def load_close_series(csv_path: Path) -> pd.Series:
    df = pd.read_csv(csv_path)
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    df = df.dropna(subset=["ts", "close"])
    df["date"] = df["ts"].dt.normalize()
    s = df.set_index("date")["close"].astype(float)
    return s[~s.index.duplicated(keep="last")].sort_index()


def load_root_floors() -> dict[str, float]:
    floors: dict[str, float] = {}
    with BOARD_A_CONSUMER_MAP.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            regime = row["regime"]
            if regime in {"Bull", "Bear", "Sideways", "Crisis", "Manipulation"}:
                floors[regime] = float(row["confidence_floor"])
    return floors


def load_source_roots() -> pd.DataFrame:
    df = pd.read_csv(
        SOURCE_REGIME_CSV,
        usecols=["date", "ticker", "regime_label", "regime_confidence"],
        parse_dates=["date"],
    )
    df = df[df["ticker"] == SOURCE_TICKER].copy()
    if df.empty:
        raise RuntimeError(f"no source rows for {SOURCE_TICKER}")
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    df["parent_regime_root"] = df["regime_label"].map(lambda v: v if v in ROOTS else "Crisis")
    df["regime_confidence"] = pd.to_numeric(df["regime_confidence"], errors="coerce").fillna(0.0)
    return df.sort_values("date").reset_index(drop=True)


class RootLookup:
    def __init__(self, source: pd.DataFrame, root_floors: dict[str, float]) -> None:
        self.dates = source["date"].to_numpy(dtype="datetime64[ns]")
        self.roots = source["parent_regime_root"].to_numpy()
        self.source_confidence = source["regime_confidence"].to_numpy()
        self.root_floors = root_floors

    def lookup(self, value: Any) -> dict[str, Any]:
        date = pd.Timestamp(value).tz_localize(None).normalize().to_datetime64()
        pos = int(np.searchsorted(self.dates, date, side="right") - 1)
        if pos < 0:
            return {
                "parent_regime_root": "Unlabeled",
                "parent_regime_confidence_floor": 0.0,
                "source_ticker_confidence": 0.0,
                "root_lookup_status": "missing_before_source_panel",
            }
        root = str(self.roots[pos])
        return {
            "parent_regime_root": root,
            "parent_regime_confidence_floor": self.root_floors.get(root, 0.0),
            "source_ticker_confidence": float(self.source_confidence[pos]),
            "root_lookup_status": "source_panel_daily_asof",
        }


def branch_path(root: str, variant_id: str) -> str:
    if root == "Bull":
        return f"{root} -> TrendExpansion -> VRPCompressionCarry -> {RECIPE_ID}:{variant_id}"
    if root == "Bear":
        return f"{root} -> BearMarketDrawdown -> VRPCompressionRiskOffRebound -> {RECIPE_ID}:{variant_id}"
    if root == "Sideways":
        return f"{root} -> RangeConsolidation -> VRPLowVolCarry -> {RECIPE_ID}:{variant_id}"
    if root == "Crisis":
        return f"{root} -> ExtremeStress -> ShortVolSuppression -> {RECIPE_ID}:{variant_id}"
    return "Manipulation(scoped) -> DirectEventOverlayMissing -> no_direct_event_rows -> suppress_or_abstain"


def load_indicators(
    feather_path: Path,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
    iv_pr: pd.Series,
    hv_pr: pd.Series,
    vvix_pr: pd.Series,
) -> pd.DataFrame:
    df = pd.read_feather(feather_path)
    df["date"] = pd.to_datetime(df["date"], unit="ms", utc=True)
    df = df.set_index("date").sort_index().loc[start:end].copy()
    if df.empty:
        return df
    df["ema21"] = df["close"].ewm(span=21, adjust=False).mean()
    df["ema89"] = df["close"].ewm(span=89, adjust=False).mean()
    df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()
    df["ema600"] = df["close"].ewm(span=600, adjust=False).mean()
    df["body_green"] = df["close"] > df["open"]
    df["hour_utc"] = df.index.hour
    candle_dates = df.index.normalize()
    df["iv_pct_rank_252"] = pd.Series(candle_dates.map(iv_pr), index=df.index).ffill()
    df["hv_pct_rank_252"] = pd.Series(candle_dates.map(hv_pr), index=df.index).ffill()
    df["vvix_pct_rank_252"] = pd.Series(candle_dates.map(vvix_pr), index=df.index).ffill()
    df["long_trend"] = df["ema200"] > df["ema600"]
    df["local_trend"] = (df["ema21"] > df["ema89"]) & (df["close"] > df["ema89"])
    df["exit_signal"] = (df["iv_pct_rank_252"] > 0.55) | (df["close"] < df["ema89"])
    return df


def variant_entry_mask(df: pd.DataFrame, variant: dict[str, Any]) -> pd.Series:
    liquid = (df["hour_utc"] >= int(variant["start_hour"])) & (df["hour_utc"] <= int(variant["end_hour"]))
    trend = df["close"] > df["ema89"]
    if bool(variant["require_long_or_local_trend"]):
        trend = trend & (df["long_trend"] | df["local_trend"])
    else:
        trend = trend & df["local_trend"]
    body = df["body_green"] if bool(variant["require_body_green"]) else pd.Series(True, index=df.index)
    return (
        liquid
        & trend
        & (df["iv_pct_rank_252"] < float(variant["iv_lt"]))
        & (df["hv_pct_rank_252"] < float(variant["hv_lt"]))
        & (df["vvix_pct_rank_252"] < float(variant["vvix_lt"]))
        & body
    )


def simulate(df: pd.DataFrame, entry_signal: pd.Series) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    closes = df["close"].to_numpy()
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    es = entry_signal.fillna(False).to_numpy()
    xs = df["exit_signal"].fillna(False).to_numpy()
    ts = df.index.to_numpy()
    trades: list[dict[str, Any]] = []
    in_pos = False
    entry_idx = -1
    entry_price = 0.0
    peak = 0.0
    trail = False
    for i in range(len(df)):
        if not in_pos:
            if es[i]:
                in_pos = True
                entry_idx = i
                entry_price = float(closes[i])
                peak = float(closes[i])
                trail = False
            continue
        peak = max(peak, float(highs[i]))
        if not trail and (peak / entry_price - 1.0) >= TRAILING_OFFSET:
            trail = True
        sl = entry_price * (1.0 + STOPLOSS)
        tp = peak * (1.0 - TRAILING_STOP) if trail else 0.0
        eff = max(sl, tp)
        reason = None
        exit_price = float(closes[i])
        if float(lows[i]) <= eff:
            reason = "stop"
            exit_price = eff
        elif xs[i]:
            reason = "exit"
        if reason is not None:
            trades.append(
                {
                    "open_date": pd.Timestamp(ts[entry_idx]),
                    "close_date": pd.Timestamp(ts[i]),
                    "profit_ratio": exit_price / entry_price - 1.0,
                    "exit_reason": reason,
                    "trade_duration_min": (pd.Timestamp(ts[i]) - pd.Timestamp(ts[entry_idx])).total_seconds() / 60.0,
                }
            )
            in_pos = False
            entry_idx = -1
            entry_price = 0.0
            peak = 0.0
            trail = False
    return pd.DataFrame(trades)


def annual_metrics(values: np.ndarray) -> dict[str, float]:
    if len(values) == 0:
        return {"mean": 0.0, "win_rate": 0.0, "sum": 0.0}
    return {
        "mean": float(values.mean()),
        "win_rate": float((values > 0.0).mean()),
        "sum": float(values.sum()),
    }


def bootstrap_lcb(values: np.ndarray, *, seed: int = 190356) -> float:
    if len(values) == 0:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(3000, len(values)), replace=True)
    means = draws.mean(axis=1)
    return float(np.quantile(means, 0.05))


def max_drawdown_from_returns(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    equity = np.cumsum(values)
    peak = np.maximum.accumulate(equity)
    drawdown = peak - equity
    return float(drawdown.max()) if len(drawdown) else 0.0


def estimate_pbo(root: str, variant_rows: list[dict[str, Any]]) -> tuple[float, str]:
    scoped = [r for r in variant_rows if r["parent_regime_root"] == root]
    folds = sorted({int(r["year_fold"]) for r in scoped})
    variants = sorted({r["variant_id"] for r in scoped})
    if len(folds) < MIN_TEST_FOLDS or len(variants) < 3:
        return 1.0, "not_identifiable_lt4_folds_or_lt3_variants"
    matrix: dict[str, dict[int, float]] = {}
    for variant in variants:
        matrix[variant] = {}
        for fold in folds:
            vals = [
                float(r["profit_ratio_net"])
                for r in scoped
                if r["variant_id"] == variant and int(r["year_fold"]) == fold
            ]
            matrix[variant][fold] = float(sum(vals))
    splits: list[tuple[list[int], list[int]]] = []
    split_size = max(1, len(folds) // 2)
    for train_folds in itertools.combinations(folds, split_size):
        train = set(train_folds)
        test = [fold for fold in folds if fold not in train]
        if test:
            splits.append((list(train), test))
    if not splits:
        return 1.0, "not_identifiable_no_train_test_splits"
    overfit = 0
    for train, test in splits:
        train_scores = {v: float(np.mean([matrix[v][fold] for fold in train])) for v in variants}
        winner = max(train_scores.items(), key=lambda item: item[1])[0]
        test_scores = {v: float(np.mean([matrix[v][fold] for fold in test])) for v in variants}
        if test_scores[winner] < float(np.median(list(test_scores.values()))):
            overfit += 1
    return float(overfit / len(splits)), "simple_cscv_variant_year_fold_proxy"


def summarize_variant_root(
    root: str,
    variant_id: str,
    rows: list[dict[str, Any]],
    all_variant_rows: list[dict[str, Any]],
    pbo: float,
    pbo_method: str,
) -> dict[str, Any]:
    returns = np.array([float(r["profit_ratio_net"]) for r in rows], dtype=float)
    outside = np.array(
        [
            float(r["profit_ratio_net"])
            for r in all_variant_rows
            if r["variant_id"] == variant_id and r["parent_regime_root"] != root
        ],
        dtype=float,
    )
    n = int(len(returns))
    folds = sorted({int(r["year_fold"]) for r in rows})
    fold_sums: list[float] = []
    fold_counts: list[int] = []
    for fold in folds:
        vals = np.array([float(r["profit_ratio_net"]) for r in rows if int(r["year_fold"]) == fold], dtype=float)
        fold_sums.append(float(vals.sum()))
        fold_counts.append(int(len(vals)))
    mean_return = float(returns.mean()) if n else 0.0
    win_rate = float((returns > 0.0).mean()) if n else 0.0
    edge_lcb = bootstrap_lcb(returns)
    stressed = returns - EXTRA_ROUND_TRIP_COST_FOR_2X_FEE
    stressed_lcb = bootstrap_lcb(stressed)
    cost_stress_survival = bool(n and stressed.sum() > 0.0 and stressed_lcb > 0.0)
    std = float(returns.std(ddof=1)) if n > 1 else 0.0
    dsr_proxy = float(mean_return / std * math.sqrt(n)) if std > 0.0 else 0.0
    tail_loss_p95 = float(max(0.0, -np.quantile(returns, 0.05))) if n else 0.0
    branch_mdd = max_drawdown_from_returns(returns)
    outside_mean = float(outside.mean()) if len(outside) else 0.0
    if mean_return > 0.0 and outside_mean <= 0.0:
        specificity_ratio = 999.0
    elif outside_mean > 0.0:
        specificity_ratio = float(mean_return / outside_mean)
    else:
        specificity_ratio = 0.0
    fold_positive_rate = float(sum(1 for v in fold_sums if v > 0.0) / len(fold_sums)) if fold_sums else 0.0
    min_trades_per_fold = int(min(fold_counts)) if fold_counts else 0

    edge_score = min(max(edge_lcb / TARGET_EDGE, 0.0), 1.0)
    fold_score = fold_positive_rate
    depth_score = min(max(n / MIN_TOTAL_TRADES, 0.0), 1.0)
    dsr_score = min(max(dsr_proxy / TARGET_DSR, 0.0), 1.0)
    pbo_score = 1.0 - min(max(pbo / 0.25, 0.0), 1.0)
    cost_score = 1.0 if cost_stress_survival else 0.0
    drawdown_score = 1.0 - min(max(branch_mdd / DRAWDOWN_BUDGET, 0.0), 1.0)
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

    failures: list[str] = []
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
        "regime_profit_branch_path": branch_path(root, variant_id),
        "total_trades": n,
        "test_folds": len(folds),
        "folds": ",".join(str(f) for f in folds),
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
        "max_drawdown_trade_equity_proxy": branch_mdd,
        "regime_specificity_ratio": specificity_ratio,
        "outside_mean_profit_ratio_net": outside_mean,
        "rc_spa": rc_spa,
        "promotion_level": "reject" if failures else ("research_watch" if rc_spa < 75 else "stable_candidate"),
        "hard_gate_result": "pass" if not failures else "fail:" + "|".join(dict.fromkeys(failures)),
        "downstream_consumption_status": (
            "not_started:blocked_by_branch_rc_spa_hard_gates"
            if failures
            else "eligible_for_pre_bayes_bbn_catboost_execution_tree_probe"
        ),
    }


def summarize_root(root: str, all_variant_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if root == "Manipulation(scoped)":
        summary = summarize_variant_root(root, "no_direct_event_rows", [], all_variant_rows, 1.0, "no_direct_event_rows")
        summary["regime_profit_branch_path"] = branch_path(root, "no_direct_event_rows")
        summary["hard_gate_result"] = (
            "fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|"
            "reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|"
            "reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|"
            "reject_rc_spa_below_60"
        )
        return summary, []

    pbo, pbo_method = estimate_pbo(root, all_variant_rows)
    variant_summaries = []
    for variant in VARIANTS:
        variant_id = str(variant["variant_id"])
        rows = [
            r
            for r in all_variant_rows
            if r["parent_regime_root"] == root and r["variant_id"] == variant_id
        ]
        variant_summaries.append(summarize_variant_root(root, variant_id, rows, all_variant_rows, pbo, pbo_method))
    selected = max(variant_summaries, key=lambda row: (float(row["rc_spa"]), int(row["total_trades"])))
    return selected, variant_summaries


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def git_ref(path: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def build_trade_row(
    *,
    trade: dict[str, Any],
    market: str,
    timeframe: str,
    variant_id: str,
    lookup: RootLookup,
) -> dict[str, Any]:
    opened = pd.Timestamp(trade["open_date"])
    closed = pd.Timestamp(trade["close_date"])
    root = lookup.lookup(opened)
    parent_root = root["parent_regime_root"]
    profit_ratio = float(trade.get("profit_ratio", 0.0) or 0.0)
    return {
        "run_id": RUN_ID,
        "recipe_id": RECIPE_ID,
        "variant_id": variant_id,
        "market": market,
        "timeframe": timeframe,
        "open_date": opened.isoformat(),
        "close_date": closed.isoformat(),
        "open_session_date": opened.tz_localize(None).normalize().date().isoformat(),
        "profit_ratio": profit_ratio,
        "profit_ratio_net": profit_ratio,
        "net_return_R": profit_ratio,
        "win": profit_ratio > 0.0,
        "exit_reason": str(trade.get("exit_reason", "")),
        "trade_duration_min": float(trade.get("trade_duration_min", 0.0) or 0.0),
        "parent_regime_root": parent_root,
        "parent_regime_confidence_floor": root["parent_regime_confidence_floor"],
        "source_ticker_confidence": root["source_ticker_confidence"],
        "root_lookup_status": root["root_lookup_status"],
        "manipulation_overlay_state": "not_consumed_no_direct_event_rows",
        "sub_regime_tags": {
            "Bull": "TrendExpansion",
            "Bear": "BearMarketDrawdown",
            "Sideways": "RangeConsolidation",
            "Crisis": "ExtremeStress",
        }.get(parent_root, "Unlabeled"),
        "sub_sub_regime_or_profit_factor": {
            "Bull": "VRPCompressionCarry",
            "Bear": "VRPCompressionRiskOffRebound",
            "Sideways": "VRPLowVolCarry",
            "Crisis": "ShortVolSuppression",
        }.get(parent_root, "Unlabeled"),
        "profit_factor_family": "options_hedging",
        "profit_factor_leaf": variant_id,
        "regime_profit_branch_path": branch_path(parent_root, variant_id),
        "regime_profit_branch_path_version": SCHEMA_VERSION,
        "trade_or_bar_horizon": f"{timeframe}_trade",
        "allowed_action": "research_only_until_all_required_root_branches_pass",
        "suppression_rule": "suppress_if_branch_rc_spa_or_pbo_fails",
        "year_fold": int(opened.year),
    }


def write_report(
    report: dict[str, Any],
    panel_summaries: list[dict[str, Any]],
    branch_summaries: list[dict[str, Any]],
) -> None:
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    panel_lines = [
        "| Market | TF | Variant | Bars | Signals | Trades | Mean | Win Rate | Net R |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in panel_summaries:
        panel_lines.append(
            f"| {row['market']} | {row['timeframe']} | `{row['variant_id']}` | {row['bars']} | "
            f"{row['signal_bars']} | {row['trades']} | {row['mean_profit_ratio']:.6f} | "
            f"{row['win_rate']:.4f} | {row['net_return_R']:.6f} |"
        )
    branch_lines = [
        "| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in branch_summaries:
        branch_lines.append(
            f"| {row['parent_regime_root']} | `{row['selected_variant_id']}` | {row['total_trades']} | "
            f"{row['test_folds']} | {row['min_trades_per_test_fold']} | "
            f"{row['fold_positive_rate']:.4f} | {row['bootstrap_edge_lcb_5pct']:.6f} | "
            f"{row['pbo']:.3f} | {row['dsr']:.4f} | {row['rc_spa']:.4f} | "
            f"`{row['hard_gate_result']}` |"
        )
    lines = [
        "# VRP V2.5 Root-Branch RC-SPA v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{report['decision']['gate_result']}`",
        f"- Stable profit score: `{report['decision']['stable_profit_score']:.4f}`",
        f"- Selected trade rows: `{report['decision']['selected_trade_rows']}`",
        f"- Variant matrix rows: `{report['decision']['variant_matrix_trade_rows']}`",
        f"- Branch paths evaluated: `{report['decision']['branch_paths_evaluated']}`",
        f"- Branch paths passed: `{report['decision']['branch_paths_passed']}`",
        f"- Selected root trade counts: `{report['decision']['selected_root_trade_counts']}`",
        f"- Matrix root trade counts: `{report['decision']['matrix_root_trade_counts']}`",
        f"- Downstream consumption: `{report['decision']['downstream_consumption']}`",
        f"- Primary blocker: {report['decision']['primary_blocker']}",
        "",
        "## Panel / Variant Matrix",
        "",
        *panel_lines,
        "",
        "## Selected Branch Summary",
        "",
        *branch_lines,
        "",
        "## Inputs",
        "",
        f"- NQ/timeframe and cross-market feathers: `{DATA_DIR}`",
        f"- Volatility sidecars: `{PROBE_DIR}`",
        f"- Board A consumer map: `{rel(BOARD_A_CONSUMER_MAP)}`",
        f"- Source root schedule: `{SOURCE_REGIME_CSV}` / `{SOURCE_TICKER}`",
        "",
        "## Artifacts",
        "",
        f"- Report JSON: `{rel(REPORT_JSON)}`",
        f"- Selected trade rows: `{rel(SELECTED_ROWS_CSV)}`",
        f"- All variant rows: `{rel(ALL_ROWS_CSV)}`",
        f"- Branch summary: `{rel(SUMMARY_CSV)}`",
        f"- Panel summary: `{rel(PANEL_SUMMARY_CSV)}`",
        f"- Fail-closed downstream summary: `{rel(FAIL_CLOSED_MD)}`",
        f"- Assertions: `{rel(ASSERTIONS)}`",
        "",
        "## Next",
        "",
        f"- {report['decision']['next_action']}",
    ]
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    for path in [OUT_DIR, CHECK_DIR, FAIL_CLOSED_DIR]:
        path.mkdir(parents=True, exist_ok=True)

    required_inputs = [QQQ_IV_CSV, QQQ_HV_CSV, VVIX_CSV, VIX_CSV, VIX3M_CSV, SOURCE_REGIME_CSV, BOARD_A_CONSUMER_MAP]
    missing = [str(path) for path in required_inputs if not path.exists() or path.stat().st_size == 0]
    missing += [str(path) for _, _, path, _, _ in PANELS if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError("missing required inputs: " + ", ".join(missing))

    iv = load_close_series(QQQ_IV_CSV)
    hv = load_close_series(QQQ_HV_CSV)
    vvix = load_close_series(VVIX_CSV)
    iv_pr = iv.rolling(252, min_periods=128).rank(pct=True)
    hv_pr = hv.rolling(252, min_periods=128).rank(pct=True)
    vvix_pr = vvix.rolling(252, min_periods=128).rank(pct=True)

    root_floors = load_root_floors()
    source_roots = load_source_roots()
    lookup = RootLookup(source_roots, root_floors)

    all_rows: list[dict[str, Any]] = []
    panel_summaries: list[dict[str, Any]] = []
    for market, timeframe, feather, start, end in PANELS:
        df = load_indicators(feather, start=start, end=end, iv_pr=iv_pr, hv_pr=hv_pr, vvix_pr=vvix_pr)
        for variant in VARIANTS:
            variant_id = str(variant["variant_id"])
            mask = variant_entry_mask(df, variant) if not df.empty else pd.Series(dtype=bool)
            trades = simulate(df, mask)
            rows = [
                build_trade_row(
                    trade={k: to_jsonable(v) for k, v in record.items()},
                    market=market,
                    timeframe=timeframe,
                    variant_id=variant_id,
                    lookup=lookup,
                )
                for record in trades.to_dict(orient="records")
            ]
            all_rows.extend(rows)
            metrics = annual_metrics(np.array([float(r["profit_ratio_net"]) for r in rows], dtype=float))
            panel_summaries.append(
                {
                    "market": market,
                    "timeframe": timeframe,
                    "variant_id": variant_id,
                    "bars": int(len(df)),
                    "signal_bars": int(mask.sum()) if len(mask) else 0,
                    "trades": int(len(rows)),
                    "mean_profit_ratio": metrics["mean"],
                    "win_rate": metrics["win_rate"],
                    "net_return_R": metrics["sum"],
                }
            )

    branch_summaries: list[dict[str, Any]] = []
    variant_summaries: list[dict[str, Any]] = []
    selected_rows: list[dict[str, Any]] = []
    for root in REQUIRED_PATHS:
        selected, variants = summarize_root(root, all_rows)
        branch_summaries.append(selected)
        variant_summaries.extend(variants)
        selected_variant = selected["selected_variant_id"]
        selected_rows.extend(
            [
                r
                for r in all_rows
                if r["parent_regime_root"] == root and r["variant_id"] == selected_variant
            ]
        )

    passed = [row for row in branch_summaries if row["hard_gate_result"] == "pass"]
    max_score = max(float(row["rc_spa"]) for row in branch_summaries) if branch_summaries else 0.0
    selected_counts = {root: 0 for root in REQUIRED_PATHS}
    for row in selected_rows:
        selected_counts[row["parent_regime_root"]] = selected_counts.get(row["parent_regime_root"], 0) + 1
    selected_counts["Manipulation(scoped)"] = 0
    matrix_counts = {root: 0 for root in REQUIRED_PATHS}
    for row in all_rows:
        matrix_counts[row["parent_regime_root"]] = matrix_counts.get(row["parent_regime_root"], 0) + 1
    matrix_counts["Manipulation(scoped)"] = 0

    root_failures = [
        f"{row['parent_regime_root']}={row['hard_gate_result']}"
        for row in branch_summaries
        if row["hard_gate_result"] != "pass"
    ]
    all_required_pass = len(passed) == len(REQUIRED_PATHS)
    gate_result = "pass" if all_required_pass else "fail:required_root_branch_hard_gates_failed"
    downstream = (
        "not_started:blocked_by_branch_rc_spa_hard_gates"
        if not all_required_pass
        else "eligible_for_pre_bayes_bbn_catboost_execution_tree_probe"
    )
    primary_blocker = (
        "all required branch hard gates passed"
        if all_required_pass
        else "; ".join(root_failures)
    )
    next_action = (
        "B5: run Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree branch consumption."
        if all_required_pass
        else "B2R-repeat: keep VRP as fail-closed evidence; next slice needs direct scoped Manipulation rows and a branch family that repairs the listed root failures without relaxing RC-SPA."
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "run_root": rel(RUN_ROOT),
        "repo_git_ref": git_ref(REPO_ROOT),
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "recipe_id": RECIPE_ID,
        "inputs": {
            "data_dir": str(DATA_DIR),
            "probe_dir": str(PROBE_DIR),
            "source_regime_csv": str(SOURCE_REGIME_CSV),
            "source_ticker": SOURCE_TICKER,
            "board_a_consumer_map": rel(BOARD_A_CONSUMER_MAP),
        },
        "decision": {
            "gate_result": gate_result,
            "stable_profit_score": max_score,
            "selected_trade_rows": len(selected_rows),
            "variant_matrix_trade_rows": len(all_rows),
            "branch_paths_evaluated": len(branch_summaries),
            "branch_paths_passed": len(passed),
            "selected_root_trade_counts": selected_counts,
            "matrix_root_trade_counts": matrix_counts,
            "downstream_consumption": downstream,
            "primary_blocker": primary_blocker,
            "next_action": next_action,
        },
        "branch_summaries": branch_summaries,
        "variant_summaries": variant_summaries,
        "panel_summaries": panel_summaries,
        "artifacts": {
            "report_json": rel(REPORT_JSON),
            "report_md": rel(REPORT_MD),
            "selected_rows_csv": rel(SELECTED_ROWS_CSV),
            "all_rows_csv": rel(ALL_ROWS_CSV),
            "summary_csv": rel(SUMMARY_CSV),
            "panel_summary_csv": rel(PANEL_SUMMARY_CSV),
            "assertions": rel(ASSERTIONS),
            "fail_closed_summary": rel(FAIL_CLOSED_MD),
        },
    }

    write_csv(ALL_ROWS_CSV, all_rows)
    write_csv(SELECTED_ROWS_CSV, selected_rows)
    write_csv(SUMMARY_CSV, branch_summaries)
    write_csv(PANEL_SUMMARY_CSV, panel_summaries)
    write_report(report, panel_summaries, branch_summaries)

    FAIL_CLOSED_MD.write_text(
        "\n".join(
            [
                "# VRP V2.5 ict-engine Fail-Closed Summary v1",
                "",
                f"Run id: `{RUN_ID}`.",
                "",
                f"- Branch RC-SPA gate: `{gate_result}`",
                f"- Downstream consumption: `{downstream}`",
                "- Pre-Bayes / BBN / CatBoost / execution-tree were not started because required branch hard gates did not all pass.",
                "- This is a fail-closed readback, not a promoted profitability packet.",
                "",
                f"Primary blocker: {primary_blocker}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertion_lines = [
        f"run_id={RUN_ID}",
        f"variant_matrix_trade_rows={len(all_rows)}",
        f"selected_trade_rows={len(selected_rows)}",
        f"branch_paths_evaluated={len(branch_summaries)}",
        f"branch_paths_passed={len(passed)}",
        f"gate_result={gate_result}",
        f"downstream_consumption={downstream}",
        "artifacts_exist=true",
    ]
    ASSERTIONS.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
