#!/usr/bin/env python3
"""Board B Tomac NQ root-aware variant matrix.

Additive experiment artifact. Generates run-local Freqtrade strategy variants,
runs them through the existing Auto-Quant Tomac synthetic NQ/USD runner, joins
Board A source-root labels per trade, and scores branch-path RC-SPA with a
simple variant/fold PBO proxy.
"""

from __future__ import annotations

import contextlib
import csv
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from freqtrade.configuration import Configuration
from freqtrade.enums import RunMode
from freqtrade.optimize.backtesting import Backtesting


RUN_ID = "20260511T184529+0800-codex-board-b-tomac-nq-variant-matrix-v1"
SCHEMA_VERSION = "board-b-tomac-nq-variant-matrix/v1"
RECIPE_ID = "TomacNQRootAwareVariantMatrixV1"
PAIR = "NQ/USD"
SOURCE_TICKER = "^IXIC"
ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
CALENDAR_FOLDS = [
    ("2011_2014", "2011-01-01", "2014-12-31"),
    ("2015_2018", "2015-01-01", "2018-12-31"),
    ("2019_2021", "2019-01-01", "2021-12-31"),
    ("2022_2023", "2022-01-01", "2023-12-31"),
    ("2024_2025", "2024-01-01", "2025-12-31"),
]
VARIANTS = [
    {
        "class_name": "TomacNQVariantBaseline",
        "variant_id": "baseline",
        "breakout_window": 24,
        "breakdown_window": 24,
        "killzone_start": 13,
        "killzone_end": 15,
        "ema_fast": 21,
        "ema_slow": 89,
        "stoploss": -0.020,
        "trail": 0.005,
        "trail_offset": 0.010,
        "trend_mode": "strict",
    },
    {
        "class_name": "TomacNQVariantTightTrail",
        "variant_id": "tight_trail",
        "breakout_window": 24,
        "breakdown_window": 18,
        "killzone_start": 13,
        "killzone_end": 16,
        "ema_fast": 21,
        "ema_slow": 89,
        "stoploss": -0.015,
        "trail": 0.003,
        "trail_offset": 0.006,
        "trend_mode": "strict",
    },
    {
        "class_name": "TomacNQVariantDenseSession",
        "variant_id": "dense_session",
        "breakout_window": 12,
        "breakdown_window": 12,
        "killzone_start": 12,
        "killzone_end": 17,
        "ema_fast": 13,
        "ema_slow": 55,
        "stoploss": -0.020,
        "trail": 0.004,
        "trail_offset": 0.008,
        "trend_mode": "strict",
    },
    {
        "class_name": "TomacNQVariantConservativeTrend",
        "variant_id": "conservative_trend",
        "breakout_window": 48,
        "breakdown_window": 24,
        "killzone_start": 13,
        "killzone_end": 15,
        "ema_fast": 34,
        "ema_slow": 144,
        "stoploss": -0.012,
        "trail": 0.004,
        "trail_offset": 0.008,
        "trend_mode": "strict",
    },
    {
        "class_name": "TomacNQVariantLooseCrisis",
        "variant_id": "loose_crisis",
        "breakout_window": 8,
        "breakdown_window": 8,
        "killzone_start": 13,
        "killzone_end": 20,
        "ema_fast": 8,
        "ema_slow": 34,
        "stoploss": -0.030,
        "trail": 0.006,
        "trail_offset": 0.012,
        "trend_mode": "loose",
    },
    {
        "class_name": "TomacNQVariantBearSidewaysDense",
        "variant_id": "bear_sideways_dense",
        "breakout_window": 6,
        "breakdown_window": 6,
        "killzone_start": 10,
        "killzone_end": 20,
        "ema_fast": 8,
        "ema_slow": 34,
        "stoploss": -0.018,
        "trail": 0.003,
        "trail_offset": 0.006,
        "trend_mode": "loose",
    },
    {
        "class_name": "TomacNQVariantFullDayTrend",
        "variant_id": "full_day_trend",
        "breakout_window": 24,
        "breakdown_window": 18,
        "killzone_start": 0,
        "killzone_end": 23,
        "ema_fast": 21,
        "ema_slow": 89,
        "stoploss": -0.020,
        "trail": 0.004,
        "trail_offset": 0.008,
        "trend_mode": "strict",
    },
]

EXTRA_ROUND_TRIP_COST = 0.002
MIN_TOTAL_TRADES = 100
MIN_TEST_FOLDS = 4
MIN_TRADES_PER_FOLD = 10
FOLD_POSITIVE_RATE_MIN = 0.75
TARGET_EDGE = 0.005
TARGET_DSR = 1.0
TAIL_LOSS_BUDGET = 0.25
DRAWDOWN_BUDGET = 0.25
MIN_SPECIFICITY_RATIO = 1.20


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot find repo root from {start}")


RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = find_repo_root(Path(__file__).resolve())
AUTO_QUANT_ROOT = Path("/Users/thrill3r/Auto-Quant")
AUTO_QUANT_USER_DATA = AUTO_QUANT_ROOT / "user_data"
AUTO_QUANT_DATA = AUTO_QUANT_USER_DATA / "data"
AUTO_QUANT_CONFIG = AUTO_QUANT_ROOT / "config.tomac.json"
SOURCE_REGIME_CSV = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
BOARD_A_CONSUMER_MAP = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/"
    "regime_factor_consumer_map_v1.csv"
)
BOARD_B = REPO_ROOT / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"

STRATEGY_DIR = RUN_ROOT / "strategy"
OUT_DIR = RUN_ROOT / "branch-rc-spa"
CHECK_DIR = RUN_ROOT / "checks"
LOG_DIR = RUN_ROOT / "logs"
STRATEGY_FILE = STRATEGY_DIR / "TomacNQRootAwareVariantMatrixV1.py"
TRADES_CSV = OUT_DIR / "tomac_nq_variant_matrix_branch_trades_v1.csv"
SUMMARY_CSV = OUT_DIR / "tomac_nq_variant_matrix_branch_rc_spa_summary_v1.csv"
VARIANT_FOLD_CSV = OUT_DIR / "tomac_nq_variant_matrix_variant_fold_returns_v1.csv"
VARIANT_RESULT_CSV = OUT_DIR / "tomac_nq_variant_matrix_variant_results_v1.csv"
REPORT_JSON = OUT_DIR / "tomac_nq_variant_matrix_report_v1.json"
REPORT_MD = OUT_DIR / "tomac_nq_variant_matrix_report_v1.md"
ASSERTIONS = CHECK_DIR / "tomac_nq_variant_matrix_v1_assertions.out"


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def setup_imports() -> None:
    sys.path.insert(0, str(AUTO_QUANT_ROOT))


def load_tomac_runner():
    setup_imports()
    import run_tomac  # type: ignore

    return run_tomac


def write_strategy_file() -> None:
    STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
    base = r'''from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy, informative
from pandas import DataFrame


class _TomacNQVariantBase(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 100}
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 250

    breakout_window = 24
    breakdown_window = 24
    killzone_start = 13
    killzone_end = 15
    ema_fast_period = 21
    ema_slow_period = 89
    trend_mode = "strict"

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=self.ema_fast_period)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=self.ema_slow_period)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["high_n"] = dataframe["high"].rolling(self.breakout_window).max().shift(1)
        dataframe["low_n"] = dataframe["low"].rolling(self.breakdown_window).min().shift(1)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["hour_utc"] = dataframe["date"].dt.hour
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        in_window = (
            (dataframe["hour_utc"] >= self.killzone_start)
            & (dataframe["hour_utc"] <= self.killzone_end)
        )
        breakout = dataframe["close"] > dataframe["high_n"]
        if self.trend_mode == "loose":
            trend = dataframe["ema_fast_4h"] >= (dataframe["ema_slow_4h"] * 0.985)
        else:
            trend = dataframe["ema_fast_4h"] > dataframe["ema_slow_4h"]
        dataframe.loc[in_window & breakout & trend, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        breakdown = dataframe["close"] < dataframe["low_n"]
        trend_break = dataframe["ema_fast_4h"] < dataframe["ema_slow_4h"]
        dataframe.loc[breakdown | trend_break, "exit_long"] = 1
        return dataframe
'''
    classes = []
    for variant in VARIANTS:
        classes.append(
            f"""
class {variant['class_name']}(_TomacNQVariantBase):
    stoploss = {variant['stoploss']!r}
    trailing_stop = True
    trailing_stop_positive = {variant['trail']!r}
    trailing_stop_positive_offset = {variant['trail_offset']!r}
    trailing_only_offset_is_reached = True
    breakout_window = {variant['breakout_window']!r}
    breakdown_window = {variant['breakdown_window']!r}
    killzone_start = {variant['killzone_start']!r}
    killzone_end = {variant['killzone_end']!r}
    ema_fast_period = {variant['ema_fast']!r}
    ema_slow_period = {variant['ema_slow']!r}
    trend_mode = {variant['trend_mode']!r}
"""
        )
    STRATEGY_FILE.write_text(base + "\n".join(classes), encoding="utf-8")


def build_config(strategy_name: str) -> dict[str, Any]:
    base = json.loads(AUTO_QUANT_CONFIG.read_text(encoding="utf-8"))
    base["exchange"]["pair_whitelist"] = [PAIR]
    base["exchange"]["skip_pair_validation"] = True
    base["stake_currency"] = "USD"
    base["timerange"] = "20110101-20251231"
    base["max_open_trades"] = 1
    args = {
        "config": [str(AUTO_QUANT_CONFIG)],
        "user_data_dir": str(AUTO_QUANT_USER_DATA),
        "datadir": str(AUTO_QUANT_DATA),
        "strategy": strategy_name,
        "strategy_path": str(STRATEGY_DIR),
        "timerange": "20110101-20251231",
        "export": "none",
        "exportfilename": None,
        "cache": "none",
    }
    config = Configuration(args, RunMode.BACKTEST).get_config()
    for key, value in base.items():
        if key != "exchange":
            config[key] = value
    config["exchange"].update(base["exchange"])
    config["pairlists"] = [{"method": "StaticPairList"}]
    return config


def run_backtest(variant: dict[str, Any]) -> dict[str, Any]:
    run_tomac = load_tomac_runner()
    strategy_name = variant["class_name"]
    config = build_config(strategy_name)
    log_path = LOG_DIR / f"freqtrade_backtest_{variant['variant_id']}.out"
    err_path = LOG_DIR / f"freqtrade_backtest_{variant['variant_id']}.err"
    with log_path.open("w", encoding="utf-8") as out, err_path.open("w", encoding="utf-8") as err:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            exchange = run_tomac._build_exchange_with_synthetic_pairs(config)
            bt = Backtesting(config, exchange=exchange)
            bt.start()
    strategy_result = bt.results.get("strategy", {}).get(strategy_name, {}) or {}
    metrics = run_tomac.extract_metrics(bt.results, strategy_name)
    return {
        "variant_id": variant["variant_id"],
        "strategy_name": strategy_name,
        "log_path": rel(log_path),
        "stderr_path": rel(err_path),
        "aggregate_metrics": metrics["aggregate"],
        "per_pair_metrics": metrics["per_pair"],
        "trades": strategy_result.get("trades", []) or [],
    }


def load_source_roots() -> pd.DataFrame:
    df = pd.read_csv(
        SOURCE_REGIME_CSV,
        usecols=["date", "ticker", "regime_label", "regime_confidence"],
        parse_dates=["date"],
    )
    df = df[df["ticker"] == SOURCE_TICKER].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    df["parent_regime_root"] = df["regime_label"].map(
        lambda value: value if value in ROOTS else "Crisis"
    )
    return df.sort_values("date").reset_index(drop=True)


class RootLookup:
    def __init__(self, source: pd.DataFrame) -> None:
        self.dates = source["date"].to_numpy(dtype="datetime64[ns]")
        self.roots = source["parent_regime_root"].to_numpy()
        self.confidence = source["regime_confidence"].to_numpy()

    def lookup(self, value: Any) -> dict[str, Any]:
        date = pd.Timestamp(value).tz_localize(None).normalize().to_datetime64()
        pos = int(np.searchsorted(self.dates, date, side="right") - 1)
        if pos < 0:
            return {
                "parent_regime_root": "Unlabeled",
                "parent_regime_confidence_floor": 0.0,
                "root_lookup_status": "missing_before_source_panel",
            }
        return {
            "parent_regime_root": str(self.roots[pos]),
            "parent_regime_confidence_floor": float(self.confidence[pos]),
            "root_lookup_status": "source_ticker_asof_daily",
        }


def branch_path(root: str) -> str:
    if root == "Bull":
        return f"{root} -> TrendExpansion -> TomacVariantMatrix -> {RECIPE_ID}"
    if root == "Bear":
        return f"{root} -> BearMarketDrawdown -> TomacVariantMatrix -> {RECIPE_ID}"
    if root == "Sideways":
        return f"{root} -> RangeConsolidation -> TomacVariantMatrix -> {RECIPE_ID}"
    if root == "Crisis":
        return f"{root} -> ExtremeStress -> TomacVariantMatrix -> {RECIPE_ID}"
    return "Manipulation(scoped) -> DirectEventOverlayMissing -> no_direct_event_rows -> suppress_or_abstain"


def fold_for(value: Any) -> str:
    ts = pd.Timestamp(value).tz_localize(None)
    for label, start, end in CALENDAR_FOLDS:
        if pd.Timestamp(start) <= ts <= pd.Timestamp(end):
            return label
    return "outside_fold"


def clean_trade(trade: dict[str, Any], variant: dict[str, Any], lookup: RootLookup) -> dict[str, Any]:
    open_date = pd.Timestamp(trade["open_date"])
    close_date = pd.Timestamp(trade["close_date"])
    root = lookup.lookup(open_date)
    profit_ratio = float(trade.get("profit_ratio", 0.0) or 0.0)
    parent_root = root["parent_regime_root"]
    return {
        "run_id": RUN_ID,
        "recipe_id": RECIPE_ID,
        "variant_id": variant["variant_id"],
        "strategy_name": variant["class_name"],
        "pair": str(trade.get("pair", "")),
        "open_date": open_date.isoformat(),
        "close_date": close_date.isoformat(),
        "fold": fold_for(open_date),
        "profit_ratio": profit_ratio,
        "net_return_R": profit_ratio,
        "win": profit_ratio > 0.0,
        "exit_reason": str(trade.get("exit_reason", "")),
        "trade_duration_min": float(trade.get("trade_duration", 0.0) or 0.0),
        "parent_regime_root": parent_root,
        "parent_regime_confidence_floor": root["parent_regime_confidence_floor"],
        "root_lookup_status": root["root_lookup_status"],
        "regime_profit_branch_path": branch_path(parent_root),
        "regime_profit_branch_path_version": "board-b/v1",
        "source_ticker": SOURCE_TICKER,
        "allowed_action": "research_only_until_branch_rc_spa_variant_matrix_passes",
        "suppression_rule": "suppress_if_branch_rc_spa_fails",
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def bootstrap_lcb(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    rng = np.random.default_rng(184529)
    means = [float(rng.choice(values, size=len(values), replace=True).mean()) for _ in range(1000)]
    return float(np.quantile(means, 0.05))


def dsr(values: np.ndarray) -> float:
    if len(values) < 2:
        return 0.0
    std = float(values.std(ddof=1))
    if std <= 1e-12:
        return 0.0
    return float(values.mean() / std * math.sqrt(len(values)))


def max_drawdown(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    equity = np.cumsum(values)
    peak = np.maximum.accumulate(equity)
    return float(np.max(peak - equity))


def fold_matrix(rows: list[dict[str, Any]], root: str) -> list[dict[str, Any]]:
    out = []
    branch = [row for row in rows if row["parent_regime_root"] == root]
    for variant in VARIANTS:
        variant_rows = [row for row in branch if row["variant_id"] == variant["variant_id"]]
        for label, _, _ in CALENDAR_FOLDS:
            fold_rows = [row for row in variant_rows if row["fold"] == label]
            values = np.array([float(row["net_return_R"]) for row in fold_rows], dtype=float)
            out.append(
                {
                    "parent_regime_root": root,
                    "variant_id": variant["variant_id"],
                    "fold": label,
                    "trades": int(len(values)),
                    "net_return_R": float(values.sum()) if len(values) else 0.0,
                    "mean_R": float(values.mean()) if len(values) else 0.0,
                }
            )
    return out


def pbo_for(matrix: list[dict[str, Any]]) -> tuple[float, str]:
    variants = sorted({row["variant_id"] for row in matrix})
    folds = [label for label, _, _ in CALENDAR_FOLDS]
    if len(variants) < 3 or len(folds) < 4:
        return 1.0, "not_identifiable_lt3_variants_or_lt4_folds"
    overfit = 0
    tested = 0
    for fold in folds:
        train_scores = {}
        test_scores = {}
        for variant in variants:
            train = [
                row["net_return_R"]
                for row in matrix
                if row["variant_id"] == variant and row["fold"] != fold
            ]
            test = [
                row["net_return_R"]
                for row in matrix
                if row["variant_id"] == variant and row["fold"] == fold
            ]
            train_scores[variant] = float(np.mean(train)) if train else 0.0
            test_scores[variant] = float(test[0]) if test else 0.0
        selected = max(train_scores, key=train_scores.get)
        selected_test = test_scores[selected]
        median_test = float(np.median(list(test_scores.values())))
        tested += 1
        if selected_test <= median_test or selected_test <= 0.0:
            overfit += 1
    return overfit / tested if tested else 1.0, "simple_variant_fold_proxy"


def rc_spa_score(
    lcb: float,
    fold_positive_rate: float,
    total: int,
    d: float,
    pbo: float,
    cost_ok: bool,
    drawdown: float,
    specificity_ratio: float,
) -> float:
    def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
        return max(low, min(high, value))

    edge_score = clamp(lcb / TARGET_EDGE)
    fold_score = fold_positive_rate
    depth_score = clamp(total / MIN_TOTAL_TRADES)
    dsr_score = clamp(d / TARGET_DSR)
    pbo_score = 1.0 - clamp(pbo / 0.25)
    cost_score = 1.0 if cost_ok else 0.0
    drawdown_score = 1.0 - clamp(drawdown / DRAWDOWN_BUDGET)
    specificity_score = clamp((specificity_ratio - 1.0) / 0.5)
    return 100.0 * (
        0.20 * edge_score
        + 0.15 * fold_score
        + 0.15 * depth_score
        + 0.15 * dsr_score
        + 0.10 * pbo_score
        + 0.10 * cost_score
        + 0.10 * drawdown_score
        + 0.05 * specificity_score
    )


def branch_summary_for(root: str, rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    branch_rows = [row for row in rows if row["parent_regime_root"] == root]
    values = np.array([float(row["net_return_R"]) for row in branch_rows], dtype=float)
    total = int(len(values))
    net = float(values.sum()) if total else 0.0
    mean = float(values.mean()) if total else 0.0
    lcb = bootstrap_lcb(values)
    fold_rows = []
    fold_nets = []
    fold_counts = []
    for label, _, _ in CALENDAR_FOLDS:
        vals = np.array(
            [float(row["net_return_R"]) for row in branch_rows if row["fold"] == label],
            dtype=float,
        )
        fold_nets.append(float(vals.sum()) if len(vals) else 0.0)
        fold_counts.append(int(len(vals)))
    test_folds = len(CALENDAR_FOLDS)
    min_fold_trades = min(fold_counts) if fold_counts else 0
    fold_positive_rate = sum(1 for value in fold_nets if value > 0.0) / test_folds
    stressed = net - EXTRA_ROUND_TRIP_COST * total
    cost_ok = stressed > 0.0
    d = dsr(values)
    win_rate = float((values > 0.0).mean()) if total else 0.0
    tail_loss_p95 = float(abs(np.quantile(values, 0.05))) if total else 0.0
    drawdown = max_drawdown(values)
    outside = np.array(
        [
            float(row["net_return_R"])
            for row in rows
            if row["parent_regime_root"] != root
        ],
        dtype=float,
    )
    outside_mean = float(outside.mean()) if len(outside) else 0.0
    if mean > 0.0 and outside_mean <= 0.0:
        specificity_ratio = 999.0
    elif mean > 0.0 and outside_mean > 0.0:
        specificity_ratio = mean / outside_mean
    else:
        specificity_ratio = 0.0
    matrix = fold_matrix(rows, root)
    pbo, pbo_method = pbo_for(matrix)
    failures: list[str] = []
    if total < MIN_TOTAL_TRADES:
        failures.append("reject_thin_trades")
    if test_folds < MIN_TEST_FOLDS:
        failures.append("reject_insufficient_test_folds")
    if min_fold_trades < MIN_TRADES_PER_FOLD:
        failures.append("reject_fold_trade_depth")
    if fold_positive_rate < FOLD_POSITIVE_RATE_MIN:
        failures.append("reject_fold_inconsistency")
    if lcb <= 0.0:
        failures.append("reject_no_positive_edge")
    if not cost_ok:
        failures.append("reject_cost_fragile")
    if pbo > 0.25:
        failures.append("reject_overfit_risk")
    if d <= 0.0:
        failures.append("reject_dsr_nonpositive")
    if tail_loss_p95 > TAIL_LOSS_BUDGET:
        failures.append("reject_tail_risk")
    if specificity_ratio < MIN_SPECIFICITY_RATIO:
        failures.append("reject_no_regime_specificity")
    score = rc_spa_score(lcb, fold_positive_rate, total, d, pbo, cost_ok, drawdown, specificity_ratio)
    if score < 60.0:
        failures.append("reject_rc_spa_below_60")
    summary = {
        "parent_regime_root": root,
        "regime_profit_branch_path": branch_path(root),
        "total_trades": total,
        "variant_count": len(VARIANTS),
        "win_rate": win_rate,
        "net_return_R": net,
        "mean_R": mean,
        "outside_mean_R": outside_mean,
        "regime_specificity_ratio": specificity_ratio,
        "bootstrap_edge_lcb_5pct": lcb,
        "stressed_2x_cost_net_R": stressed,
        "cost_stress_result": "pass" if cost_ok else "fail",
        "test_folds": test_folds,
        "min_trades_per_test_fold": min_fold_trades,
        "fold_positive_rate": fold_positive_rate,
        "fold_net_returns": fold_nets,
        "fold_trade_counts": fold_counts,
        "pbo": pbo,
        "pbo_method": pbo_method,
        "dsr": d,
        "tail_loss_p95": tail_loss_p95,
        "max_drawdown_trade_equity_proxy": drawdown,
        "rc_spa": score,
        "promotion_level": "reject" if failures else "stable_candidate",
        "hard_gate_result": "pass" if not failures else "fail:" + "|".join(failures),
        "failure_reasons": failures,
        "downstream_consumption_status": "not_started:blocked_by_branch_rc_spa_hard_gates"
        if failures
        else "not_started:rc_spa_candidate_needs_downstream",
    }
    return summary, matrix


def summarize(rows: list[dict[str, Any]], variant_results: list[dict[str, Any]]) -> dict[str, Any]:
    branch_summaries = []
    matrix_rows = []
    for root in ROOTS + ["Manipulation(scoped)"]:
        summary, matrix = branch_summary_for(root, rows)
        branch_summaries.append(summary)
        matrix_rows.extend(matrix)
    passes = [row for row in branch_summaries if row["hard_gate_result"] == "pass"]
    max_score = max((row["rc_spa"] for row in branch_summaries), default=0.0)
    root_counts = {row["parent_regime_root"]: row["total_trades"] for row in branch_summaries}
    if passes:
        gate = "pass:branch_paths_available_for_downstream"
        downstream = "not_started:rc_spa_candidate"
        blocker = "At least one branch path passed RC-SPA; downstream consumption must preserve the same branch path before promotion."
        next_action = "B5: pass the promoted branch path through Pre-Bayes, BBN, CatBoost/path-ranker, and execution tree checks."
    else:
        gate = "fail:all_branch_paths_failed_rc_spa_hard_gates"
        downstream = "not_started:blocked_by_branch_rc_spa_hard_gates"
        blocker = (
            "Tomac NQ variant matrix ran real Auto-Quant/Freqtrade variants and estimated PBO, "
            "but no root branch passed RC-SPA hard gates; downstream promotion remains blocked."
        )
        next_action = (
            "B2R-repeat: extend direct Crisis/scoped Manipulation rows or test a different "
            "root-aware NQ family before downstream branch consumption."
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_root": rel(RUN_ROOT),
        "board_b": rel(BOARD_B),
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "accepted_regime_artifact": rel(BOARD_A_CONSUMER_MAP),
        "recipe_id": RECIPE_ID,
        "pair": PAIR,
        "source_ticker": SOURCE_TICKER,
        "auto_quant": {
            "root": str(AUTO_QUANT_ROOT),
            "config": str(AUTO_QUANT_CONFIG),
            "data_path": str(AUTO_QUANT_DATA / "NQ_USD-1h.feather"),
            "generated_strategy_path": rel(STRATEGY_FILE),
        },
        "variant_specs": VARIANTS,
        "variant_results": [{k: v for k, v in result.items() if k != "trades"} for result in variant_results],
        "branch_summaries": branch_summaries,
        "decision": {
            "board_state": "rejected" if not passes else "stable_candidate",
            "gate_result": gate,
            "stable_profit_score": max_score,
            "branch_paths_evaluated": len(branch_summaries),
            "branch_paths_passed": len(passes),
            "total_variant_trade_rows": len(rows),
            "root_trade_counts": root_counts,
            "downstream_consumption": downstream,
            "primary_blocker": blocker,
            "next_action": next_action,
        },
        "completion": {
            "runtime_code_changed": False,
            "auto_quant_checkout_changed": False,
            "raw_auto_quant_data_committed": False,
            "thresholds_relaxed": False,
            "downstream_runtime_consumed_branch_path": False,
        },
        "variant_fold_matrix": matrix_rows,
    }


def write_report(report: dict[str, Any]) -> None:
    variant_rows = []
    for result in report["variant_results"]:
        metrics = result["aggregate_metrics"]
        variant_rows.append(
            {
                "variant_id": result["variant_id"],
                "strategy_name": result["strategy_name"],
                "trade_count": int(metrics.get("trade_count", 0)),
                "win_rate_pct": float(metrics.get("win_rate_pct", 0.0)),
                "total_profit_pct": float(metrics.get("total_profit_pct", 0.0)),
                "sharpe": float(metrics.get("sharpe", 0.0)),
                "profit_factor": float(metrics.get("profit_factor", 0.0)),
                "log_path": result["log_path"],
            }
        )
    write_csv(VARIANT_RESULT_CSV, variant_rows)
    write_csv(VARIANT_FOLD_CSV, report["variant_fold_matrix"])
    summary_rows = [
        {
            "parent_regime_root": row["parent_regime_root"],
            "total_trades": row["total_trades"],
            "variant_count": row["variant_count"],
            "test_folds": row["test_folds"],
            "min_fold_trades": row["min_trades_per_test_fold"],
            "fold_positive_rate": row["fold_positive_rate"],
            "edge_lcb_5pct": row["bootstrap_edge_lcb_5pct"],
            "pbo": row["pbo"],
            "dsr": row["dsr"],
            "tail_loss_p95": row["tail_loss_p95"],
            "specificity_ratio": row["regime_specificity_ratio"],
            "rc_spa": row["rc_spa"],
            "hard_gate_result": row["hard_gate_result"],
            "branch_path": row["regime_profit_branch_path"],
        }
        for row in report["branch_summaries"]
    ]
    write_csv(SUMMARY_CSV, summary_rows)
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Tomac NQ Root-Aware Variant Matrix v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{report['decision']['gate_result']}`",
        f"- Stable profit score: `{report['decision']['stable_profit_score']:.4f}`",
        f"- Variant trade rows: `{report['decision']['total_variant_trade_rows']}`",
        f"- Branch paths evaluated: `{report['decision']['branch_paths_evaluated']}`",
        f"- Branch paths passed: `{report['decision']['branch_paths_passed']}`",
        f"- Root trade counts: `{report['decision']['root_trade_counts']}`",
        f"- Downstream consumption: `{report['decision']['downstream_consumption']}`",
        f"- Primary blocker: {report['decision']['primary_blocker']}",
        "",
        "## Auto-Quant / Freqtrade Variant Readback",
        "",
        "| Variant | Strategy | Trades | Win rate % | Profit % | Sharpe | PF | Log |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in variant_rows:
        lines.append(
            f"| `{row['variant_id']}` | `{row['strategy_name']}` | {row['trade_count']} | "
            f"{row['win_rate_pct']:.3f} | {row['total_profit_pct']:.3f} | "
            f"{row['sharpe']:.4f} | {row['profit_factor']:.3f} | `{row['log_path']}` |"
        )
    lines.extend(
        [
            "",
            "## Branch Summary",
            "",
            "| Root | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | Specificity | RC-SPA | Gate |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in report["branch_summaries"]:
        lines.append(
            f"| {row['parent_regime_root']} | {row['total_trades']} | {row['test_folds']} | "
            f"{row['min_trades_per_test_fold']} | {row['fold_positive_rate']:.4f} | "
            f"{row['bootstrap_edge_lcb_5pct']:.6f} | {row['pbo']:.2f} | "
            f"{row['dsr']:.4f} | {row['regime_specificity_ratio']:.3f} | "
            f"{row['rc_spa']:.4f} | `{row['hard_gate_result']}` |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Report JSON: `{rel(REPORT_JSON)}`",
            f"- Generated strategy: `{rel(STRATEGY_FILE)}`",
            f"- Trade rows: `{rel(TRADES_CSV)}`",
            f"- Branch summary: `{rel(SUMMARY_CSV)}`",
            f"- Variant fold matrix: `{rel(VARIANT_FOLD_CSV)}`",
            f"- Variant result summary: `{rel(VARIANT_RESULT_CSV)}`",
            f"- Assertions: `{rel(ASSERTIONS)}`",
            "",
            "## Next",
            "",
            f"- {report['decision']['next_action']}",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def git_ref() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(AUTO_QUANT_ROOT), "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def main() -> int:
    for path in [STRATEGY_DIR, OUT_DIR, CHECK_DIR, LOG_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    write_strategy_file()
    lookup = RootLookup(load_source_roots())
    variant_results = []
    rows = []
    for variant in VARIANTS:
        result = run_backtest(variant)
        variant_results.append(result)
        rows.extend([clean_trade(trade, variant, lookup) for trade in result["trades"]])
    write_csv(TRADES_CSV, rows)
    report = summarize(rows, variant_results)
    report["auto_quant"]["pinned_ref"] = git_ref()
    write_report(report)
    assertions = [
        f"run_id={RUN_ID}",
        f"recipe_id={RECIPE_ID}",
        f"pair={PAIR}",
        f"variant_count={len(VARIANTS)}",
        f"variant_trade_rows={len(rows)}",
        f"gate_result={report['decision']['gate_result']}",
        f"stable_profit_score={report['decision']['stable_profit_score']:.6f}",
        f"branch_paths_passed={report['decision']['branch_paths_passed']}",
        f"root_trade_counts={report['decision']['root_trade_counts']}",
        f"report_json={rel(REPORT_JSON)}",
    ]
    if len(rows) == 0:
        assertions.append("ASSERT_FAIL:no_variant_trade_rows")
    if report["decision"]["gate_result"].startswith("pass:"):
        assertions.append("ASSERT_WARN:downstream_required_before_promotion")
    ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "run_id": RUN_ID,
                "recipe_id": RECIPE_ID,
                "variants": len(VARIANTS),
                "variant_trade_rows": len(rows),
                "stable_profit_score": report["decision"]["stable_profit_score"],
                "gate_result": report["decision"]["gate_result"],
                "report": rel(REPORT_MD),
            },
            indent=2,
        )
    )
    return 0 if not any(line.startswith("ASSERT_FAIL") for line in assertions) else 1


if __name__ == "__main__":
    raise SystemExit(main())
