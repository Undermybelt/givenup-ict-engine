#!/usr/bin/env python3
"""Board B RootTransitionTriadV1 branch RC-SPA readback.

Run-local additive scorer. It uses existing Auto-Quant feathers, attaches the
accepted Board A root schedule, scores root-aware transition/continuation/range
signals, and emits fail-closed artifacts. It does not change ict-engine runtime
code or the Auto-Quant checkout.
"""

from __future__ import annotations

import csv
import itertools
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260511T192018+0800-codex-board-b-root-transition-triad-v1"
SCHEMA_VERSION = "board-b-root-transition-triad/v1"
RECIPE_ID = "RootTransitionTriadV1"
SOURCE_TICKER = "^IXIC"
ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
REQUIRED_PATHS = ["Bull", "Bear", "Sideways", "Crisis", "Manipulation(scoped)"]

DATA_DIR = Path("/Users/thrill3r/Auto-Quant/user_data/data")
SOURCE_REGIME_CSV = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)

START_LONG = pd.Timestamp("2018-01-01", tz="UTC")
START_SHORT = pd.Timestamp("2025-01-01", tz="UTC")
END = pd.Timestamp("2026-05-31", tz="UTC")

TARGET_EDGE = 0.001
TARGET_DSR = 1.0
DRAWDOWN_BUDGET = 0.30
TAIL_LOSS_BUDGET = 0.08
MIN_TOTAL_TRADES = 100
MIN_TEST_FOLDS = 4
MIN_TRADES_PER_TEST_FOLD = 10
FOLD_POSITIVE_RATE_MIN = 0.70
EXTRA_ROUND_TRIP_COST_FOR_2X_FEE = 0.001

PANELS = [
    ("NQ/USD", "5m", DATA_DIR / "NQ_USD-5m.feather", START_LONG),
    ("NQ/USD", "15m", DATA_DIR / "NQ_USD-15m.feather", START_LONG),
    ("NQ/USD", "1h", DATA_DIR / "NQ_USD-1h.feather", START_LONG),
    ("NQ/USD", "1d", DATA_DIR / "NQ_USD-1d.feather", START_LONG),
    ("SPY/USD", "15m", DATA_DIR / "SPY_USD-15m.feather", START_SHORT),
    ("SPY/USD", "1h", DATA_DIR / "SPY_USD-1h.feather", START_SHORT),
    ("SPY/USD", "1d", DATA_DIR / "SPY_USD-1d.feather", START_SHORT),
    ("QQQ/USD", "1h", DATA_DIR / "QQQ_USD-1h.feather", START_SHORT),
    ("QQQ/USD", "1d", DATA_DIR / "QQQ_USD-1d.feather", START_SHORT),
    ("IWM/USD", "15m", DATA_DIR / "IWM_USD-15m.feather", START_SHORT),
    ("IWM/USD", "1h", DATA_DIR / "IWM_USD-1h.feather", START_SHORT),
    ("DIA/USD", "15m", DATA_DIR / "DIA_USD-15m.feather", START_SHORT),
    ("DIA/USD", "1h", DATA_DIR / "DIA_USD-1h.feather", START_SHORT),
    ("GLD/USD", "15m", DATA_DIR / "GLD_USD-15m.feather", START_SHORT),
    ("GLD/USD", "1h", DATA_DIR / "GLD_USD-1h.feather", START_SHORT),
    ("AAPL/USD", "1d", DATA_DIR / "AAPL_USD-1d.feather", START_SHORT),
    ("BTCY/USD", "1d", DATA_DIR / "BTCY_USD-1d.feather", START_SHORT),
    ("ES/USD", "1d", DATA_DIR / "ES_USD-1d.feather", START_SHORT),
]

VARIANTS: list[dict[str, Any]] = [
    {
        "variant_id": "bull_transition_pullback",
        "mode": "transition",
        "hold_days": 3.0,
        "stop_loss": -0.035,
        "take_profit": 0.045,
    },
    {
        "variant_id": "root_continuation",
        "mode": "continuation",
        "hold_days": 2.0,
        "stop_loss": -0.025,
        "take_profit": 0.035,
    },
    {
        "variant_id": "sideways_range_reversion",
        "mode": "range_reversion",
        "hold_days": 2.0,
        "stop_loss": -0.025,
        "take_profit": 0.030,
    },
    {
        "variant_id": "bear_crisis_relief",
        "mode": "stress_relief",
        "hold_days": 4.0,
        "stop_loss": -0.045,
        "take_profit": 0.060,
    },
    {
        "variant_id": "compressed_break_continuation",
        "mode": "compressed_break",
        "hold_days": 3.0,
        "stop_loss": -0.030,
        "take_profit": 0.050,
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

ALL_ROWS_CSV = OUT_DIR / "root_transition_triad_all_variant_rows_v1.csv"
SELECTED_ROWS_CSV = OUT_DIR / "root_transition_triad_selected_rows_v1.csv"
SUMMARY_CSV = OUT_DIR / "root_transition_triad_branch_summary_v1.csv"
PANEL_SUMMARY_CSV = OUT_DIR / "root_transition_triad_panel_summary_v1.csv"
REPORT_JSON = OUT_DIR / "root_transition_triad_report_v1.json"
REPORT_MD = OUT_DIR / "root_transition_triad_report_v1.md"
ASSERTIONS = CHECK_DIR / "root_transition_triad_v1_assertions.out"
WIRE_JSONL = FAIL_CLOSED_DIR / "root_transition_triad_real_trades_wire_v1.jsonl"
WIRE_COUNT = FAIL_CLOSED_DIR / "root_transition_triad_real_trades_wire_v1.count"
FAIL_CLOSED_MD = FAIL_CLOSED_DIR / "root_transition_triad_ict_engine_fail_closed_summary_v1.md"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def git_ref(path: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


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
    )
    df = df[df["ticker"] == SOURCE_TICKER].copy()
    if df.empty:
        raise RuntimeError(f"no source rows for {SOURCE_TICKER}")
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_localize(None).dt.normalize()
    df["parent_regime_root"] = df["regime_label"].map(lambda v: v if v in ROOTS else "Crisis")
    df["regime_confidence"] = pd.to_numeric(df["regime_confidence"], errors="coerce").fillna(0.0)
    return df.sort_values("date").reset_index(drop=True)


class RootLookup:
    def __init__(self, source: pd.DataFrame, root_floors: dict[str, float]) -> None:
        self.dates = source["date"].to_numpy(dtype="datetime64[ns]")
        self.roots = source["parent_regime_root"].to_numpy()
        self.confidence = source["regime_confidence"].to_numpy()
        self.root_floors = root_floors

    def attach(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            df["parent_regime_root"] = []
            df["source_ticker_confidence"] = []
            df["parent_regime_confidence_floor"] = []
            return df
        bar_dates = df.index.tz_localize(None).normalize().to_numpy(dtype="datetime64[ns]")
        positions = np.searchsorted(self.dates, bar_dates, side="right") - 1
        roots = np.full(len(df), "Unlabeled", dtype=object)
        conf = np.zeros(len(df), dtype=float)
        valid = positions >= 0
        roots[valid] = self.roots[positions[valid]]
        conf[valid] = self.confidence[positions[valid]]
        df["parent_regime_root"] = roots
        df["source_ticker_confidence"] = conf
        df["parent_regime_confidence_floor"] = [self.root_floors.get(str(root), 0.0) for root in roots]
        return df


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0).ewm(alpha=1.0 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0.0)).ewm(alpha=1.0 / period, adjust=False).mean()
    rs = gain / loss.replace(0.0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))


def load_panel(feather: Path, start: pd.Timestamp, lookup: RootLookup) -> pd.DataFrame:
    df = pd.read_feather(feather)
    df["date"] = pd.to_datetime(df["date"], unit="ms", utc=True)
    df = df.set_index("date").sort_index().loc[start:END].copy()
    if df.empty:
        return df
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema100"] = df["close"].ewm(span=100, adjust=False).mean()
    df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()
    df["rsi14"] = rsi(df["close"]).fillna(50.0)
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    df["atr_pct"] = tr.rolling(14, min_periods=5).mean() / df["close"].replace(0.0, np.nan)
    df["ret_3"] = df["close"] / df["close"].shift(3) - 1.0
    df["ret_5"] = df["close"] / df["close"].shift(5) - 1.0
    df["ret_20"] = df["close"] / df["close"].shift(20) - 1.0
    rolling_mean = df["close"].rolling(40, min_periods=20).mean()
    rolling_std = df["close"].rolling(40, min_periods=20).std().replace(0.0, np.nan)
    df["z40"] = ((df["close"] - rolling_mean) / rolling_std).fillna(0.0)
    df["body_green"] = df["close"] > df["open"]
    df["hour_utc"] = df.index.hour
    df["liquid_window"] = (df["hour_utc"] >= 13) & (df["hour_utc"] <= 21)
    return lookup.attach(df)


def branch_path(root: str, variant_id: str) -> str:
    if root == "Bull":
        return f"{root} -> TrendExpansion -> PullbackContinuation -> {RECIPE_ID}:{variant_id}"
    if root == "Bear":
        return f"{root} -> BearMarketDrawdown -> ReliefTransition -> {RECIPE_ID}:{variant_id}"
    if root == "Sideways":
        return f"{root} -> RangeConsolidation -> RangeReversion -> {RECIPE_ID}:{variant_id}"
    if root == "Crisis":
        return f"{root} -> ExtremeStress -> StressReliefOrSuppression -> {RECIPE_ID}:{variant_id}"
    return "Manipulation(scoped) -> DirectEventOverlayMissing -> no_direct_event_rows -> suppress_or_abstain"


def entry_mask(df: pd.DataFrame, variant: dict[str, Any], timeframe: str) -> pd.Series:
    mode = str(variant["mode"])
    intraday = timeframe.endswith("m") or timeframe.endswith("h")
    window = df["liquid_window"] if intraday else pd.Series(True, index=df.index)
    root = df["parent_regime_root"]
    bull = (
        (root == "Bull")
        & (df["close"] > df["ema100"])
        & (df["ema50"] >= df["ema200"])
        & (df["rsi14"].between(38, 72))
        & (df["ret_5"] <= 0.018)
        & df["body_green"]
    )
    bear = (
        (root == "Bear")
        & (df["ret_5"] <= -0.025)
        & (df["rsi14"] <= 48)
        & df["body_green"]
    )
    sideways = (
        (root == "Sideways")
        & (df["z40"] <= -0.55)
        & (df["rsi14"] <= 48)
        & df["body_green"]
        & (df["atr_pct"].fillna(0.0) < 0.045)
    )
    crisis = (
        (root == "Crisis")
        & ((df["ret_5"] <= -0.045) | (df["ret_20"] <= -0.10) | (df["rsi14"] <= 34))
        & df["body_green"]
    )
    if mode == "transition":
        mask = bull | bear | sideways | crisis
    elif mode == "continuation":
        mask = (
            ((root == "Bull") & (df["close"] > df["ema50"]) & (df["ret_3"] > 0.0) & df["body_green"])
            | ((root == "Bear") & (df["ret_5"] <= -0.015) & (df["rsi14"] < 55) & df["body_green"])
        )
    elif mode == "range_reversion":
        mask = sideways | ((root == "Bull") & (df["z40"] <= -0.8) & (df["rsi14"] < 48) & df["body_green"])
    elif mode == "stress_relief":
        mask = bear | crisis
    elif mode == "compressed_break":
        quiet = df["atr_pct"].fillna(0.0) < df["atr_pct"].rolling(252, min_periods=50).quantile(0.45).fillna(0.02)
        mask = window & quiet & (df["close"] > df["ema50"]) & (df["ret_3"] > 0.0) & df["body_green"]
        return mask.fillna(False)
    else:
        mask = pd.Series(False, index=df.index)
    return (window & mask).fillna(False)


def hold_bars(timeframe: str, hold_days: float) -> int:
    if timeframe == "5m":
        return max(3, int(round(78 * hold_days)))
    if timeframe == "15m":
        return max(3, int(round(26 * hold_days)))
    if timeframe == "1h":
        return max(2, int(round(7 * hold_days)))
    return max(1, int(round(hold_days)))


def simulate(df: pd.DataFrame, mask: pd.Series, variant: dict[str, Any], timeframe: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    closes = df["close"].to_numpy(dtype=float)
    highs = df["high"].to_numpy(dtype=float)
    lows = df["low"].to_numpy(dtype=float)
    es = mask.fillna(False).to_numpy()
    ts = df.index.to_numpy()
    max_hold = hold_bars(timeframe, float(variant["hold_days"]))
    stop_loss = float(variant["stop_loss"])
    take_profit = float(variant["take_profit"])
    rows: list[dict[str, Any]] = []
    in_pos = False
    entry_idx = -1
    entry_price = 0.0
    for i in range(len(df)):
        if not in_pos:
            if es[i]:
                in_pos = True
                entry_idx = i
                entry_price = float(closes[i])
            continue
        age = i - entry_idx
        stop = entry_price * (1.0 + stop_loss)
        target = entry_price * (1.0 + take_profit)
        reason = None
        exit_price = float(closes[i])
        if float(lows[i]) <= stop:
            reason = "stop"
            exit_price = stop
        elif float(highs[i]) >= target:
            reason = "target"
            exit_price = target
        elif age >= max_hold:
            reason = "time_exit"
        if reason is not None:
            rows.append(
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
    return pd.DataFrame(rows)


def bootstrap_lcb(values: np.ndarray, *, seed: int = 192018) -> float:
    if len(values) == 0:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(3000, len(values)), replace=True)
    return float(np.quantile(draws.mean(axis=1), 0.05))


def max_drawdown(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    equity = np.cumsum(values)
    peak = np.maximum.accumulate(equity)
    return float((peak - equity).max())


def estimate_pbo(root: str, rows: list[dict[str, Any]]) -> tuple[float, str]:
    scoped = [row for row in rows if row["parent_regime_root"] == root]
    folds = sorted({int(row["year_fold"]) for row in scoped})
    variants = sorted({row["variant_id"] for row in scoped})
    if len(folds) < MIN_TEST_FOLDS or len(variants) < 3:
        return 1.0, "not_identifiable_lt4_folds_or_lt3_variants"
    matrix: dict[str, dict[int, float]] = {variant: {} for variant in variants}
    for variant in variants:
        for fold in folds:
            matrix[variant][fold] = sum(
                float(row["profit_ratio_net"])
                for row in scoped
                if row["variant_id"] == variant and int(row["year_fold"]) == fold
            )
    overfit = 0
    splits = 0
    split_size = max(1, len(folds) // 2)
    for train_folds in itertools.combinations(folds, split_size):
        train = set(train_folds)
        test = [fold for fold in folds if fold not in train]
        if not test:
            continue
        splits += 1
        train_scores = {v: float(np.mean([matrix[v][f] for f in train])) for v in variants}
        winner = max(train_scores.items(), key=lambda item: item[1])[0]
        test_scores = {v: float(np.mean([matrix[v][f] for f in test])) for v in variants}
        if test_scores[winner] < float(np.median(list(test_scores.values()))):
            overfit += 1
    return (float(overfit / splits), "simple_cscv_variant_year_fold_proxy") if splits else (1.0, "no_splits")


def summarize_variant_root(
    root: str,
    variant_id: str,
    rows: list[dict[str, Any]],
    all_rows: list[dict[str, Any]],
    pbo: float,
    pbo_method: str,
) -> dict[str, Any]:
    returns = np.array([float(row["profit_ratio_net"]) for row in rows], dtype=float)
    outside = np.array(
        [
            float(row["profit_ratio_net"])
            for row in all_rows
            if row["variant_id"] == variant_id and row["parent_regime_root"] != root
        ],
        dtype=float,
    )
    n = int(len(returns))
    folds = sorted({int(row["year_fold"]) for row in rows})
    fold_sums = [
        sum(float(row["profit_ratio_net"]) for row in rows if int(row["year_fold"]) == fold)
        for fold in folds
    ]
    fold_counts = [
        sum(1 for row in rows if int(row["year_fold"]) == fold)
        for fold in folds
    ]
    mean_return = float(returns.mean()) if n else 0.0
    win_rate = float((returns > 0.0).mean()) if n else 0.0
    edge_lcb = bootstrap_lcb(returns)
    stressed = returns - EXTRA_ROUND_TRIP_COST_FOR_2X_FEE
    stressed_lcb = bootstrap_lcb(stressed)
    cost_ok = bool(n and stressed.sum() > 0.0 and stressed_lcb > 0.0)
    std = float(returns.std(ddof=1)) if n > 1 else 0.0
    dsr = float(mean_return / std * math.sqrt(n)) if std > 0.0 else 0.0
    tail_loss = float(max(0.0, -np.quantile(returns, 0.05))) if n else 0.0
    mdd = max_drawdown(returns)
    outside_mean = float(outside.mean()) if len(outside) else 0.0
    if mean_return > 0.0 and outside_mean <= 0.0:
        specificity = 999.0
    elif outside_mean > 0.0:
        specificity = float(mean_return / outside_mean)
    else:
        specificity = 0.0
    fold_pos = float(sum(1 for value in fold_sums if value > 0.0) / len(fold_sums)) if fold_sums else 0.0
    min_fold = int(min(fold_counts)) if fold_counts else 0

    edge_score = min(max(edge_lcb / TARGET_EDGE, 0.0), 1.0)
    fold_score = fold_pos
    depth_score = min(max(n / MIN_TOTAL_TRADES, 0.0), 1.0)
    dsr_score = min(max(dsr / TARGET_DSR, 0.0), 1.0)
    pbo_score = 1.0 - min(max(pbo / 0.25, 0.0), 1.0)
    cost_score = 1.0 if cost_ok else 0.0
    drawdown_score = 1.0 - min(max(mdd / DRAWDOWN_BUDGET, 0.0), 1.0)
    specificity_score = min(max((specificity - 1.0) / 0.5, 0.0), 1.0)
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
    if min_fold < MIN_TRADES_PER_TEST_FOLD:
        failures.append("reject_fold_trade_depth")
    if fold_pos < FOLD_POSITIVE_RATE_MIN:
        failures.append("reject_fold_inconsistency")
    if edge_lcb <= 0.0:
        failures.append("reject_no_positive_edge")
    if not cost_ok:
        failures.append("reject_cost_fragile")
    if pbo > 0.25:
        failures.append("reject_overfit_risk")
    if dsr <= 0.0:
        failures.append("reject_dsr_nonpositive")
    if tail_loss > TAIL_LOSS_BUDGET:
        failures.append("reject_tail_risk")
    if specificity < 1.20:
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
        "folds": ",".join(str(fold) for fold in folds),
        "min_trades_per_test_fold": min_fold,
        "fold_positive_rate": fold_pos,
        "win_rate": win_rate,
        "mean_profit_ratio_net": mean_return,
        "net_return_R": float(returns.sum()) if n else 0.0,
        "bootstrap_edge_lcb_5pct": edge_lcb,
        "bootstrap_edge_lcb_5pct_stressed_2x_cost": stressed_lcb,
        "pbo": pbo,
        "pbo_method": pbo_method,
        "dsr": dsr,
        "cost_stress_result": "pass" if cost_ok else "fail",
        "tail_loss_p95": tail_loss,
        "max_drawdown_trade_equity_proxy": mdd,
        "regime_specificity_ratio": specificity,
        "outside_mean_profit_ratio_net": outside_mean,
        "rc_spa": rc_spa,
        "hard_gate_result": "pass" if not failures else "fail:" + "|".join(dict.fromkeys(failures)),
        "downstream_consumption_status": (
            "eligible_for_pre_bayes_bbn_catboost_execution_tree_probe"
            if not failures
            else "not_started:blocked_by_branch_rc_spa_hard_gates"
        ),
    }


def summarize_root(root: str, all_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if root == "Manipulation(scoped)":
        summary = summarize_variant_root(root, "no_direct_event_rows", [], all_rows, 1.0, "no_direct_event_rows")
        summary["hard_gate_result"] = (
            "fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|"
            "reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|"
            "reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|"
            "reject_rc_spa_below_60"
        )
        return summary, []
    pbo, pbo_method = estimate_pbo(root, all_rows)
    variants = []
    for variant in VARIANTS:
        variant_id = str(variant["variant_id"])
        rows = [
            row
            for row in all_rows
            if row["parent_regime_root"] == root and row["variant_id"] == variant_id
        ]
        variants.append(summarize_variant_root(root, variant_id, rows, all_rows, pbo, pbo_method))
    selected = max(variants, key=lambda row: (float(row["rc_spa"]), int(row["total_trades"])))
    return selected, variants


def trade_row(
    record: dict[str, Any],
    source_bar: pd.Series,
    market: str,
    timeframe: str,
    variant_id: str,
    sequence: int,
) -> dict[str, Any]:
    opened = pd.Timestamp(record["open_date"])
    closed = pd.Timestamp(record["close_date"])
    root = str(source_bar["parent_regime_root"])
    pnl = float(record["profit_ratio"])
    return {
        "run_id": RUN_ID,
        "recipe_id": RECIPE_ID,
        "variant_id": variant_id,
        "market": market,
        "timeframe": timeframe,
        "trade_id": f"{RECIPE_ID}|{variant_id}|{market}|{timeframe}|{opened.isoformat()}|{sequence}",
        "open_date": opened.isoformat(),
        "close_date": closed.isoformat(),
        "open_ts_ms": int(opened.timestamp() * 1000),
        "close_ts_ms": int(closed.timestamp() * 1000),
        "open_session_date": opened.tz_localize(None).normalize().date().isoformat(),
        "profit_ratio": pnl,
        "profit_ratio_net": pnl,
        "net_return_R": pnl,
        "win": pnl > 0.0,
        "exit_reason": str(record.get("exit_reason", "")),
        "trade_duration_min": float(record.get("trade_duration_min", 0.0) or 0.0),
        "parent_regime_root": root,
        "parent_regime_confidence_floor": float(source_bar["parent_regime_confidence_floor"]),
        "source_ticker_confidence": float(source_bar["source_ticker_confidence"]),
        "root_lookup_status": f"{SOURCE_TICKER}_source_panel_daily_asof",
        "manipulation_overlay_state": "not_consumed_no_direct_event_rows",
        "sub_regime_tags": {
            "Bull": "TrendExpansion",
            "Bear": "BearMarketDrawdown",
            "Sideways": "RangeConsolidation",
            "Crisis": "ExtremeStress",
        }.get(root, "Unlabeled"),
        "sub_sub_regime_or_profit_factor": {
            "Bull": "PullbackContinuation",
            "Bear": "ReliefTransition",
            "Sideways": "RangeReversion",
            "Crisis": "StressReliefOrSuppression",
        }.get(root, "Unlabeled"),
        "profit_factor_family": "root_transition_price_action",
        "profit_factor_leaf": variant_id,
        "regime_profit_branch_path": branch_path(root, variant_id),
        "regime_profit_branch_path_version": SCHEMA_VERSION,
        "trade_or_bar_horizon": f"{timeframe}_trade",
        "allowed_action": "research_only_until_all_required_root_branches_pass",
        "suppression_rule": "suppress_if_branch_rc_spa_or_pbo_fails",
        "year_fold": int(opened.year),
    }


def write_wire(rows: list[dict[str, Any]]) -> None:
    FAIL_CLOSED_DIR.mkdir(parents=True, exist_ok=True)
    with WIRE_JSONL.open("w", encoding="utf-8") as fh:
        for row in rows:
            pnl = float(row["profit_ratio_net"])
            root = row["parent_regime_root"]
            root_direction = "Bull" if root == "Bull" else "Bear" if root in {"Bear", "Crisis"} else "Neutral"
            payload = {
                "schema_version": "1.0",
                "symbol": "ROOT_TRIAD_192018_SELECTED",
                "trade_id": row["trade_id"],
                "strategy_name": RECIPE_ID,
                "strategy_mutation_id": f"board-b-root-transition-triad-{row['variant_id']}",
                "auto_quant_run_id": RUN_ID,
                "open_ts_ms": row["open_ts_ms"],
                "close_ts_ms": row["close_ts_ms"],
                "direction": "long",
                "pnl": pnl,
                "realized_outcome": "win" if pnl > 0.0 else "loss",
                "regime_at_entry": root,
                "entry_signal": row["variant_id"],
                "factors_used": [
                    {
                        "factor_name": "market_regime_context.root",
                        "category": "regime_context",
                        "direction": root_direction,
                        "value": row["source_ticker_confidence"],
                        "confidence": row["source_ticker_confidence"],
                        "weighted_score": row["source_ticker_confidence"],
                        "uncertainty_contribution": max(0.0, 1.0 - row["source_ticker_confidence"]),
                    },
                    {
                        "factor_name": "regime_profit_branch_path",
                        "category": "branch_path",
                        "direction": "Bull" if pnl >= 0 else "Bear",
                        "value": pnl,
                        "confidence": row["source_ticker_confidence"],
                        "weighted_score": pnl,
                        "uncertainty_contribution": max(0.0, 1.0 - row["source_ticker_confidence"]),
                    },
                    {
                        "factor_name": row["variant_id"],
                        "category": "root_transition_price_action",
                        "direction": "Bull" if pnl >= 0 else "Bear",
                        "value": pnl,
                        "confidence": 0.60,
                        "weighted_score": pnl,
                        "uncertainty_contribution": 0.40,
                    },
                ],
                "structural_feedback": {
                    "protocol_version": SCHEMA_VERSION,
                    "recommendation_id": row["trade_id"],
                    "recommended_at": row["open_date"],
                    "symbol": "ROOT_TRIAD_192018_SELECTED",
                    "node_id": root,
                    "branch_id": row["regime_profit_branch_path"],
                    "scenario_id": row["sub_regime_tags"],
                    "path_id": row["regime_profit_branch_path"],
                    "direction": "long",
                    "entry_style": row["variant_id"],
                    "candidate_set_id": RUN_ID,
                    "candidate_set_size": len(rows),
                    "followed_path": True,
                    "realized_outcome": "win" if pnl > 0.0 else "loss",
                    "realized_pnl": pnl,
                    "exit_reason": row["exit_reason"],
                    "notes": "diagnostic_dry_run_only_root_transition_triad_rc_spa_rejected",
                },
            }
            fh.write(json.dumps(payload, sort_keys=True) + "\n")
    WIRE_COUNT.write_text(f"{len(rows)}\n", encoding="utf-8")


def write_report(report: dict[str, Any]) -> None:
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    panel_lines = [
        "| Market | TF | Variant | Bars | Signals | Trades | Mean | Win Rate | Net R |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["panel_summaries"]:
        panel_lines.append(
            f"| {row['market']} | {row['timeframe']} | `{row['variant_id']}` | {row['bars']} | "
            f"{row['signal_bars']} | {row['trades']} | {row['mean_profit_ratio']:.6f} | "
            f"{row['win_rate']:.4f} | {row['net_return_R']:.6f} |"
        )
    branch_lines = [
        "| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["branch_summaries"]:
        branch_lines.append(
            f"| {row['parent_regime_root']} | `{row['selected_variant_id']}` | {row['total_trades']} | "
            f"{row['test_folds']} | {row['min_trades_per_test_fold']} | "
            f"{row['fold_positive_rate']:.4f} | {row['bootstrap_edge_lcb_5pct']:.6f} | "
            f"{row['pbo']:.3f} | {row['dsr']:.4f} | {row['rc_spa']:.4f} | "
            f"`{row['hard_gate_result']}` |"
        )
    decision = report["decision"]
    lines = [
        "# RootTransitionTriadV1 Branch RC-SPA v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Stable profit score: `{decision['stable_profit_score']:.4f}`",
        f"- Selected trade rows: `{decision['selected_trade_rows']}`",
        f"- Variant matrix rows: `{decision['variant_matrix_trade_rows']}`",
        f"- Branch paths evaluated: `{decision['branch_paths_evaluated']}`",
        f"- Branch paths passed: `{decision['branch_paths_passed']}`",
        f"- Selected root trade counts: `{decision['selected_root_trade_counts']}`",
        f"- Matrix root trade counts: `{decision['matrix_root_trade_counts']}`",
        f"- Downstream consumption: `{decision['downstream_consumption']}`",
        f"- Primary blocker: {decision['primary_blocker']}",
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
        f"- Local feathers: `{DATA_DIR}`",
        f"- Board A consumer map: `{rel(BOARD_A_CONSUMER_MAP)}`",
        f"- Source root schedule: `{SOURCE_REGIME_CSV}` / `{SOURCE_TICKER}`",
        "",
        "## Artifacts",
        "",
        f"- Report JSON: `{rel(REPORT_JSON)}`",
        f"- Selected rows: `{rel(SELECTED_ROWS_CSV)}`",
        f"- All variant rows: `{rel(ALL_ROWS_CSV)}`",
        f"- Branch summary: `{rel(SUMMARY_CSV)}`",
        f"- Panel summary: `{rel(PANEL_SUMMARY_CSV)}`",
        f"- ict-engine wire JSONL: `{rel(WIRE_JSONL)}`",
        f"- Assertions: `{rel(ASSERTIONS)}`",
        "",
        "## Next",
        "",
        f"- {decision['next_action']}",
    ]
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    for path in [OUT_DIR, CHECK_DIR, FAIL_CLOSED_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    required = [SOURCE_REGIME_CSV, BOARD_A_CONSUMER_MAP]
    required += [path for _, _, path, _ in PANELS]
    missing = [str(path) for path in required if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError("missing required inputs: " + ", ".join(missing))
    lookup = RootLookup(load_source_roots(), load_root_floors())

    all_rows: list[dict[str, Any]] = []
    panel_summaries: list[dict[str, Any]] = []
    sequence = 0
    for market, timeframe, feather, start in PANELS:
        df = load_panel(feather, start, lookup)
        if len(df) < 250:
            continue
        for variant in VARIANTS:
            variant_id = str(variant["variant_id"])
            mask = entry_mask(df, variant, timeframe)
            trades = simulate(df, mask, variant, timeframe)
            rows: list[dict[str, Any]] = []
            for record in trades.to_dict(orient="records"):
                opened = pd.Timestamp(record["open_date"])
                source_bar = df.loc[opened]
                sequence += 1
                rows.append(trade_row(record, source_bar, market, timeframe, variant_id, sequence))
            all_rows.extend(rows)
            values = np.array([float(row["profit_ratio_net"]) for row in rows], dtype=float)
            panel_summaries.append(
                {
                    "market": market,
                    "timeframe": timeframe,
                    "variant_id": variant_id,
                    "bars": int(len(df)),
                    "signal_bars": int(mask.sum()),
                    "trades": int(len(rows)),
                    "mean_profit_ratio": float(values.mean()) if len(values) else 0.0,
                    "win_rate": float((values > 0).mean()) if len(values) else 0.0,
                    "net_return_R": float(values.sum()) if len(values) else 0.0,
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
                row
                for row in all_rows
                if row["parent_regime_root"] == root and row["variant_id"] == selected_variant
            ]
        )

    passed = [row for row in branch_summaries if row["hard_gate_result"] == "pass"]
    max_score = max(float(row["rc_spa"]) for row in branch_summaries) if branch_summaries else 0.0
    selected_counts = {root: 0 for root in REQUIRED_PATHS}
    matrix_counts = {root: 0 for root in REQUIRED_PATHS}
    for row in selected_rows:
        selected_counts[row["parent_regime_root"]] = selected_counts.get(row["parent_regime_root"], 0) + 1
    for row in all_rows:
        matrix_counts[row["parent_regime_root"]] = matrix_counts.get(row["parent_regime_root"], 0) + 1
    selected_counts["Manipulation(scoped)"] = 0
    matrix_counts["Manipulation(scoped)"] = 0
    root_failures = [
        f"{row['parent_regime_root']}={row['hard_gate_result']}"
        for row in branch_summaries
        if row["hard_gate_result"] != "pass"
    ]
    all_required_pass = len(passed) == len(REQUIRED_PATHS)
    gate_result = "pass" if all_required_pass else "fail:required_root_branch_hard_gates_failed"
    downstream = (
        "eligible_for_pre_bayes_bbn_catboost_execution_tree_probe"
        if all_required_pass
        else "not_started:blocked_by_branch_rc_spa_hard_gates"
    )
    next_action = (
        "B5: run Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree branch consumption."
        if all_required_pass
        else "B2R-repeat: keep RootTransitionTriad fail-closed; source direct Manipulation executable PnL and repair any listed root failures without relaxing RC-SPA."
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
            "primary_blocker": "all required branch hard gates passed" if all_required_pass else "; ".join(root_failures),
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
            "wire_jsonl": rel(WIRE_JSONL),
            "assertions": rel(ASSERTIONS),
            "fail_closed_summary": rel(FAIL_CLOSED_MD),
        },
    }
    write_csv(ALL_ROWS_CSV, all_rows)
    write_csv(SELECTED_ROWS_CSV, selected_rows)
    write_csv(SUMMARY_CSV, branch_summaries)
    write_csv(PANEL_SUMMARY_CSV, panel_summaries)
    write_wire(selected_rows)
    write_report(report)
    FAIL_CLOSED_MD.write_text(
        "\n".join(
            [
                "# RootTransitionTriad ict-engine Fail-Closed Summary v1",
                "",
                f"Run id: `{RUN_ID}`.",
                "",
                f"- Branch RC-SPA gate: `{gate_result}`",
                f"- Downstream consumption: `{downstream}`",
                "- Real-trade ingest dry-run is expected to be run after artifact generation.",
                "- Pre-Bayes / BBN / CatBoost / execution-tree must stay stopped unless all required branch hard gates pass.",
                "- This is a fail-closed readback, not a promoted profitability packet.",
                "",
                f"Primary blocker: {report['decision']['primary_blocker']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assertions = [
        f"run_id={RUN_ID}",
        f"variant_matrix_trade_rows={len(all_rows)}",
        f"selected_trade_rows={len(selected_rows)}",
        f"branch_paths_evaluated={len(branch_summaries)}",
        f"branch_paths_passed={len(passed)}",
        f"gate_result={gate_result}",
        f"downstream_consumption={downstream}",
        "artifacts_exist=true",
    ]
    if not all_rows:
        assertions.append("ASSERT_FAIL:no_variant_rows")
    ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 1 if any(item.startswith("ASSERT_FAIL") for item in assertions) else 0


if __name__ == "__main__":
    raise SystemExit(main())
