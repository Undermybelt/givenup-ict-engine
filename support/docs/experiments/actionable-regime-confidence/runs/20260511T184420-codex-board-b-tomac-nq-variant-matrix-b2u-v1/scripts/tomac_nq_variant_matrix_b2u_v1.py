#!/usr/bin/env python3
"""Board B Tomac NQ root-aware variant matrix readback.

This additive experiment generates a run-local Freqtrade strategy, runs real
Auto-Quant/Freqtrade backtests on the existing synthetic NQ/USD data, attaches
Board A root labels, estimates a simple CSCV/PBO proxy across variants, and
writes branch-path RC-SPA evidence. It does not modify ict-engine runtime code
or the Auto-Quant checkout.
"""

from __future__ import annotations

import contextlib
import csv
import itertools
import json
import math
import os
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


RUN_ID = "20260511T184420+0800-codex-board-b-tomac-nq-variant-matrix-b2u-v1"
SCHEMA_VERSION = "board-b-tomac-nq-rootaware-variant-matrix-b2u/v1"
RECIPE_ID = "TomacNQRootAwareVariantMatrixB2U"
STRATEGY_CLASS = "TomacNQRootAwareVariantMatrixB2U"
PAIR = "NQ/USD"
SOURCE_TICKER = "^IXIC"
ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
FULL_TIMERANGE = "20110101-20251231"

VARIANTS: list[dict[str, Any]] = [
    {
        "variant_id": "tomac_baseline_bull",
        "bull_enabled": 1,
        "bear_enabled": 0,
        "sideways_enabled": 0,
        "crisis_enabled": 0,
        "bull_start_hour": 13,
        "bull_end_hour": 15,
        "bull_lookback": 24,
        "bull_atr_mult": 0.0,
        "bull_volume_mult": 0.0,
        "bear_rsi": 35.0,
        "bear_ret_24h": -0.03,
        "sideways_rsi": 40.0,
        "crisis_rsi": 55.0,
        "crisis_ret_24h": -0.03,
        "hold_hours": 96.0,
    },
    {
        "variant_id": "bull_cost_filtered",
        "bull_enabled": 1,
        "bear_enabled": 0,
        "sideways_enabled": 0,
        "crisis_enabled": 0,
        "bull_start_hour": 14,
        "bull_end_hour": 15,
        "bull_lookback": 48,
        "bull_atr_mult": 0.15,
        "bull_volume_mult": 1.05,
        "bear_rsi": 35.0,
        "bear_ret_24h": -0.03,
        "sideways_rsi": 40.0,
        "crisis_rsi": 55.0,
        "crisis_ret_24h": -0.03,
        "hold_hours": 72.0,
    },
    {
        "variant_id": "bear_sideways_reversion",
        "bull_enabled": 1,
        "bear_enabled": 1,
        "sideways_enabled": 1,
        "crisis_enabled": 0,
        "bull_start_hour": 13,
        "bull_end_hour": 15,
        "bull_lookback": 36,
        "bull_atr_mult": 0.05,
        "bull_volume_mult": 0.0,
        "bear_rsi": 48.0,
        "bear_ret_24h": -0.018,
        "sideways_rsi": 45.0,
        "crisis_rsi": 60.0,
        "crisis_ret_24h": -0.03,
        "hold_hours": 36.0,
    },
    {
        "variant_id": "crisis_dense_rebound",
        "bull_enabled": 0,
        "bear_enabled": 1,
        "sideways_enabled": 1,
        "crisis_enabled": 1,
        "bull_start_hour": 13,
        "bull_end_hour": 15,
        "bull_lookback": 24,
        "bull_atr_mult": 0.0,
        "bull_volume_mult": 0.0,
        "bear_rsi": 55.0,
        "bear_ret_24h": -0.01,
        "sideways_rsi": 52.0,
        "crisis_rsi": 82.0,
        "crisis_ret_24h": 0.02,
        "hold_hours": 18.0,
    },
    {
        "variant_id": "all_root_dense",
        "bull_enabled": 1,
        "bear_enabled": 1,
        "sideways_enabled": 1,
        "crisis_enabled": 1,
        "bull_start_hour": 12,
        "bull_end_hour": 16,
        "bull_lookback": 24,
        "bull_atr_mult": -0.05,
        "bull_volume_mult": 0.0,
        "bear_rsi": 62.0,
        "bear_ret_24h": 0.02,
        "sideways_rsi": 58.0,
        "crisis_rsi": 95.0,
        "crisis_ret_24h": 0.05,
        "hold_hours": 12.0,
    },
]

EXTRA_ROUND_TRIP_COST_FOR_2X_FEE = 0.002
TARGET_EDGE = 0.005
TARGET_DSR = 1.0
DRAWDOWN_BUDGET = 0.25
TAIL_LOSS_BUDGET = 0.25
MIN_TOTAL_TRADES = 100
MIN_TEST_FOLDS = 4
MIN_TRADES_PER_TEST_FOLD = 10
FOLD_POSITIVE_RATE_MIN = 0.75


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

OUT_DIR = RUN_ROOT / "branch-rc-spa"
CHECK_DIR = RUN_ROOT / "checks"
LOG_DIR = RUN_ROOT / "logs"
STRATEGY_DIR = RUN_ROOT / "strategy"
ROOT_SCHEDULE_PATH = STRATEGY_DIR / "board_a_ixic_root_schedule_v1.json"
TRADES_CSV = OUT_DIR / "tomac_nq_variant_matrix_selected_branch_trades_v1.csv"
VARIANT_ROWS_CSV = OUT_DIR / "tomac_nq_variant_matrix_all_variant_branch_rows_v1.csv"
SUMMARY_CSV = OUT_DIR / "tomac_nq_variant_matrix_branch_rc_spa_summary_v1.csv"
VARIANT_SUMMARY_CSV = OUT_DIR / "tomac_nq_variant_matrix_variant_summary_v1.csv"
REPORT_JSON = OUT_DIR / "tomac_nq_variant_matrix_branch_rc_spa_report_v1.json"
REPORT_MD = OUT_DIR / "tomac_nq_variant_matrix_branch_rc_spa_report_v1.md"
ASSERTIONS = CHECK_DIR / "tomac_nq_variant_matrix_b2u_v1_assertions.out"


STRATEGY_SOURCE = r'''
from datetime import timedelta
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import talib.abstract as ta
from freqtrade.strategy import IStrategy, informative
from pandas import DataFrame


class TomacNQRootAwareVariantMatrixB2U(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 100}
    stoploss = -0.02
    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.01
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 250
    _root_schedule = None

    @classmethod
    def _schedule(cls):
        if cls._root_schedule is None:
            rows = json.loads(Path(os.environ["BOARD_B_ROOT_SCHEDULE"]).read_text(encoding="utf-8"))
            df = pd.DataFrame(rows)
            df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
            cls._root_schedule = df.sort_values("date").reset_index(drop=True)
        return cls._root_schedule

    @staticmethod
    def _float_env(name: str, default: float) -> float:
        try:
            return float(os.environ.get(name, default))
        except (TypeError, ValueError):
            return default

    def _attach_root(self, dataframe: DataFrame) -> DataFrame:
        schedule = self._schedule()
        context_dates = schedule["date"].values.astype("datetime64[ns]")
        roots = schedule["parent_regime_root"].to_numpy()
        confidence = schedule["source_confidence"].to_numpy()
        bar_dates = pd.to_datetime(dataframe["date"], utc=True).dt.tz_convert(None)
        bar_dates = bar_dates.dt.normalize().values.astype("datetime64[ns]")
        positions = np.searchsorted(context_dates, bar_dates, side="right") - 1
        labels = np.full(len(dataframe), "Unlabeled", dtype=object)
        conf = np.zeros(len(dataframe), dtype=float)
        valid = positions >= 0
        labels[valid] = roots[positions[valid]]
        conf[valid] = confidence[positions[valid]]
        dataframe["parent_regime_root"] = labels
        dataframe["parent_regime_confidence_floor"] = conf
        return dataframe

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=89)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = self._attach_root(dataframe)
        max_lookback = 72
        dataframe["high_24h"] = dataframe["high"].rolling(24).max().shift(1)
        dataframe["high_36h"] = dataframe["high"].rolling(36).max().shift(1)
        dataframe["high_48h"] = dataframe["high"].rolling(48).max().shift(1)
        dataframe["high_72h"] = dataframe["high"].rolling(max_lookback).max().shift(1)
        dataframe["low_24h"] = dataframe["low"].rolling(24).min().shift(1)
        dataframe["low_36h"] = dataframe["low"].rolling(36).min().shift(1)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["sma50"] = ta.SMA(dataframe, timeperiod=50)
        dataframe["sma200"] = ta.SMA(dataframe, timeperiod=200)
        dataframe["volume_sma20"] = dataframe["volume"].rolling(20).mean()
        bb_mid = dataframe["close"].rolling(20).mean()
        bb_dev = dataframe["close"].rolling(20).std()
        dataframe["bb_mid"] = bb_mid
        dataframe["bb_lower"] = bb_mid - 2.0 * bb_dev
        dataframe["ret_24h"] = dataframe["close"] / dataframe["close"].shift(24) - 1.0
        dataframe["hour_utc"] = dataframe["date"].dt.hour
        return dataframe

    def _high_col(self) -> str:
        lookback = int(self._float_env("BOARD_B_BULL_LOOKBACK", 24))
        if lookback <= 24:
            return "high_24h"
        if lookback <= 36:
            return "high_36h"
        if lookback <= 48:
            return "high_48h"
        return "high_72h"

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        bull_enabled = self._float_env("BOARD_B_BULL_ENABLED", 1.0) > 0.5
        bear_enabled = self._float_env("BOARD_B_BEAR_ENABLED", 0.0) > 0.5
        sideways_enabled = self._float_env("BOARD_B_SIDEWAYS_ENABLED", 0.0) > 0.5
        crisis_enabled = self._float_env("BOARD_B_CRISIS_ENABLED", 0.0) > 0.5

        start_hour = int(self._float_env("BOARD_B_BULL_START_HOUR", 13))
        end_hour = int(self._float_env("BOARD_B_BULL_END_HOUR", 15))
        bull_high = dataframe[self._high_col()]
        bull = (
            bull_enabled
            & (dataframe["parent_regime_root"] == "Bull")
            & (dataframe["hour_utc"] >= start_hour)
            & (dataframe["hour_utc"] <= end_hour)
            & (dataframe["close"] > bull_high + self._float_env("BOARD_B_BULL_ATR_MULT", 0.0) * dataframe["atr"])
            & (dataframe["ema_fast_4h"] > dataframe["ema_slow_4h"])
            & (dataframe["close"] > dataframe["sma50"])
            & (
                dataframe["volume"]
                > self._float_env("BOARD_B_BULL_VOLUME_MULT", 0.0) * dataframe["volume_sma20"].fillna(0.0)
            )
        )
        bear = (
            bear_enabled
            & (dataframe["parent_regime_root"] == "Bear")
            & (dataframe["rsi"] < self._float_env("BOARD_B_BEAR_RSI", 45.0))
            & (
                (dataframe["close"] < dataframe["bb_lower"] * 1.01)
                | (dataframe["ret_24h"] < self._float_env("BOARD_B_BEAR_RET_24H", -0.02))
            )
        )
        sideways = (
            sideways_enabled
            & (dataframe["parent_regime_root"] == "Sideways")
            & (dataframe["rsi"] < self._float_env("BOARD_B_SIDEWAYS_RSI", 45.0))
            & (dataframe["close"] < dataframe["bb_mid"])
            & (dataframe["close"] > dataframe["sma200"] * 0.80)
        )
        crisis = (
            crisis_enabled
            & (dataframe["parent_regime_root"] == "Crisis")
            & (dataframe["rsi"] < self._float_env("BOARD_B_CRISIS_RSI", 70.0))
            & (
                (dataframe["close"] < dataframe["bb_mid"])
                | (dataframe["ret_24h"] < self._float_env("BOARD_B_CRISIS_RET_24H", -0.02))
            )
        )
        dataframe.loc[bull | bear | sideways | crisis, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        bull_exit = (
            (dataframe["parent_regime_root"] == "Bull")
            & ((dataframe["close"] < dataframe["ema20"]) | (dataframe["close"] < dataframe["low_24h"]))
        )
        mr_exit = (
            dataframe["parent_regime_root"].isin(["Bear", "Sideways", "Crisis"])
            & ((dataframe["close"] > dataframe["bb_mid"]) | (dataframe["rsi"] > 58))
        )
        dataframe.loc[bull_exit | mr_exit, "exit_long"] = 1
        return dataframe

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        hold_hours = self._float_env("BOARD_B_HOLD_HOURS", 72.0)
        if current_time - trade.open_date_utc >= timedelta(hours=hold_hours):
            return "rootaware_time_exit"
        return None
'''


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def setup_imports() -> None:
    sys.path.insert(0, str(AUTO_QUANT_ROOT))


def load_tomac_runner():
    setup_imports()
    import run_tomac  # type: ignore

    return run_tomac


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
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    df["parent_regime_root"] = df["regime_label"].map(lambda v: v if v in ROOTS else "Crisis")
    return df.sort_values("date").reset_index(drop=True)


def write_strategy_and_schedule(source_roots: pd.DataFrame) -> None:
    STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
    (STRATEGY_DIR / f"{STRATEGY_CLASS}.py").write_text(STRATEGY_SOURCE, encoding="utf-8")
    schedule_rows = [
        {
            "date": pd.Timestamp(row["date"]).date().isoformat(),
            "parent_regime_root": row["parent_regime_root"],
            "source_confidence": float(row["regime_confidence"]),
        }
        for row in source_roots.to_dict(orient="records")
    ]
    ROOT_SCHEDULE_PATH.write_text(
        json.dumps(schedule_rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def branch_path(root: str, variant_id: str) -> str:
    if root == "Bull":
        return f"{root} -> TrendExpansion -> TomacNQRootAwareBreakout -> {RECIPE_ID}:{variant_id}"
    if root == "Bear":
        return f"{root} -> BearMarketDrawdown -> TomacNQRootAwareRebound -> {RECIPE_ID}:{variant_id}"
    if root == "Sideways":
        return f"{root} -> RangeConsolidation -> TomacNQRootAwareRangeReversion -> {RECIPE_ID}:{variant_id}"
    if root == "Crisis":
        return f"{root} -> ExtremeStress -> TomacNQRootAwareStressReboundOrAbstain -> {RECIPE_ID}:{variant_id}"
    return "Manipulation(scoped) -> DirectEventOverlayMissing -> no_direct_event_rows -> suppress_or_abstain"


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


def apply_variant_env(variant: dict[str, Any]) -> None:
    os.environ["BOARD_B_ROOT_SCHEDULE"] = str(ROOT_SCHEDULE_PATH)
    for key, value in variant.items():
        if key == "variant_id":
            continue
        os.environ[f"BOARD_B_{key.upper()}"] = str(value)


def build_config(timerange: str) -> dict[str, Any]:
    base = json.loads(AUTO_QUANT_CONFIG.read_text(encoding="utf-8"))
    base["exchange"]["pair_whitelist"] = [PAIR]
    base["exchange"]["skip_pair_validation"] = True
    base["stake_currency"] = "USD"
    base["timerange"] = timerange
    base["max_open_trades"] = 1
    args = {
        "config": [str(AUTO_QUANT_CONFIG)],
        "user_data_dir": str(AUTO_QUANT_USER_DATA),
        "datadir": str(AUTO_QUANT_DATA),
        "strategy": STRATEGY_CLASS,
        "strategy_path": str(STRATEGY_DIR),
        "timerange": timerange,
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
    apply_variant_env(variant)
    run_tomac = load_tomac_runner()
    config = build_config(FULL_TIMERANGE)
    label = str(variant["variant_id"])
    log_path = LOG_DIR / f"freqtrade_backtest_{label}.out"
    err_path = LOG_DIR / f"freqtrade_backtest_{label}.err"
    with log_path.open("w", encoding="utf-8") as out, err_path.open("w", encoding="utf-8") as err:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            exchange = run_tomac._build_exchange_with_synthetic_pairs(config)
            bt = Backtesting(config, exchange=exchange)
            bt.start()
    strategy_result = bt.results.get("strategy", {}).get(STRATEGY_CLASS, {}) or {}
    metrics = run_tomac.extract_metrics(bt.results, STRATEGY_CLASS)
    return {
        "variant_id": label,
        "timerange": FULL_TIMERANGE,
        "log_path": rel(log_path),
        "stderr_path": rel(err_path),
        "aggregate_metrics": metrics["aggregate"],
        "trades": strategy_result.get("trades", []) or [],
    }


def to_jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except TypeError:
            pass
    return str(value)


def clean_trade(
    trade: dict[str, Any],
    lookup: RootLookup,
    root_floors: dict[str, float],
    variant_id: str,
) -> dict[str, Any]:
    opened = pd.Timestamp(trade["open_date"])
    closed = pd.Timestamp(trade["close_date"])
    root = lookup.lookup(opened)
    profit_ratio = float(trade.get("profit_ratio", 0.0) or 0.0)
    parent_root = root["parent_regime_root"]
    return {
        "run_id": RUN_ID,
        "recipe_id": RECIPE_ID,
        "strategy_class": STRATEGY_CLASS,
        "variant_id": variant_id,
        "pair": str(trade.get("pair", "")),
        "open_date": opened.isoformat(),
        "close_date": closed.isoformat(),
        "open_session_date": opened.tz_localize(None).normalize().date().isoformat(),
        "profit_ratio": profit_ratio,
        "profit_ratio_net": profit_ratio,
        "net_return_R": profit_ratio,
        "win": profit_ratio > 0,
        "exit_reason": str(trade.get("exit_reason", "")),
        "trade_duration_min": float(trade.get("trade_duration", 0.0) or 0.0),
        "parent_regime_root": parent_root,
        "parent_regime_confidence_floor": root_floors.get(parent_root, 0.0),
        "source_ticker_confidence": root["parent_regime_confidence_floor"],
        "root_lookup_status": root["root_lookup_status"],
        "regime_profit_branch_path": branch_path(parent_root, variant_id),
        "regime_profit_branch_path_version": SCHEMA_VERSION,
        "source_ticker": SOURCE_TICKER,
        "year_fold": int(opened.year),
        "allowed_action": "research_only_until_all_required_root_branches_pass",
        "suppression_rule": "suppress_if_branch_rc_spa_or_pbo_fails",
        "raw_trade": json.dumps({k: to_jsonable(v) for k, v in trade.items() if k != "orders"}, sort_keys=True),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def bootstrap_lcb(values: np.ndarray, *, seed: int = 184420) -> float:
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
    matrix: dict[str, dict[int, float]] = {}
    scoped = [r for r in variant_rows if r["parent_regime_root"] == root]
    folds = sorted({int(r["year_fold"]) for r in scoped})
    variants = sorted({r["variant_id"] for r in scoped})
    if len(folds) < MIN_TEST_FOLDS or len(variants) < 3:
        return 1.0, "not_identifiable_lt4_folds_or_lt3_variants"
    for variant in variants:
        matrix[variant] = {}
        for fold in folds:
            vals = [
                float(r["profit_ratio_net"])
                for r in scoped
                if r["variant_id"] == variant and int(r["year_fold"]) == fold
            ]
            matrix[variant][fold] = float(sum(vals))
    splits = []
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
        median_test = float(np.median(list(test_scores.values())))
        if test_scores[winner] < median_test:
            overfit += 1
    return float(overfit / len(splits)), "simple_cscv_variant_fold_proxy"


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
        variant_summaries.append(
            summarize_variant_root(root, variant_id, rows, all_variant_rows, pbo, pbo_method)
        )
    selected = max(variant_summaries, key=lambda row: (float(row["rc_spa"]), int(row["total_trades"])))
    return selected, variant_summaries


def git_ref() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(AUTO_QUANT_ROOT), "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def write_report(
    report: dict[str, Any],
    variant_run_summaries: list[dict[str, Any]],
    branch_summaries: list[dict[str, Any]],
) -> None:
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    timer_lines = [
        "| Variant | Trades | Win rate % | Profit % | Sharpe | Log |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in variant_run_summaries:
        metrics = row["aggregate_metrics"]
        timer_lines.append(
            f"| `{row['variant_id']}` | {int(metrics.get('trade_count', 0))} | "
            f"{float(metrics.get('win_rate_pct', 0.0)):.3f} | "
            f"{float(metrics.get('total_profit_pct', 0.0)):.3f} | "
            f"{float(metrics.get('sharpe', 0.0)):.4f} | `{row['log_path']}` |"
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
        "# Tomac NQ Root-Aware Variant Matrix B2U v1",
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
        "## Auto-Quant / Freqtrade Variant Matrix",
        "",
        *timer_lines,
        "",
        "## Selected Branch Summary",
        "",
        *branch_lines,
        "",
        "## Artifacts",
        "",
        f"- Report JSON: `{rel(REPORT_JSON)}`",
        f"- Selected trade rows: `{rel(TRADES_CSV)}`",
        f"- All variant rows: `{rel(VARIANT_ROWS_CSV)}`",
        f"- Branch summary: `{rel(SUMMARY_CSV)}`",
        f"- Variant summary: `{rel(VARIANT_SUMMARY_CSV)}`",
        f"- Generated strategy: `{rel(STRATEGY_DIR / (STRATEGY_CLASS + '.py'))}`",
        f"- Assertions: `{rel(ASSERTIONS)}`",
        "",
        "## Next",
        "",
        f"- {report['decision']['next_action']}",
    ]
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    for path in [OUT_DIR, CHECK_DIR, LOG_DIR, STRATEGY_DIR]:
        path.mkdir(parents=True, exist_ok=True)

    source_roots = load_source_roots()
    root_floors = load_root_floors()
    write_strategy_and_schedule(source_roots)
    lookup = RootLookup(source_roots)

    variant_run_summaries: list[dict[str, Any]] = []
    all_variant_rows: list[dict[str, Any]] = []
    backtest_log = CHECK_DIR / "tomac_nq_variant_matrix_freqtrade_backtests.out"
    backtest_err = CHECK_DIR / "tomac_nq_variant_matrix_freqtrade_backtests.err"
    with backtest_log.open("w", encoding="utf-8") as out, backtest_err.open("w", encoding="utf-8") as err:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            for variant in VARIANTS:
                result = run_backtest(variant)
                variant_run_summaries.append(
                    {k: v for k, v in result.items() if k != "trades"}
                )
                for trade in result["trades"]:
                    all_variant_rows.append(
                        clean_trade(trade, lookup, root_floors, str(variant["variant_id"]))
                    )

    write_csv(VARIANT_ROWS_CSV, all_variant_rows)

    branch_summaries: list[dict[str, Any]] = []
    all_variant_summaries: list[dict[str, Any]] = []
    selected_rows: list[dict[str, Any]] = []
    for root in [*ROOTS, "Manipulation(scoped)"]:
        selected, variants = summarize_root(root, all_variant_rows)
        branch_summaries.append(selected)
        all_variant_summaries.extend(variants)
        selected_rows.extend(
            [
                row
                for row in all_variant_rows
                if row["parent_regime_root"] == root
                and row["variant_id"] == selected["selected_variant_id"]
            ]
        )

    write_csv(TRADES_CSV, selected_rows)
    write_csv(SUMMARY_CSV, branch_summaries)
    write_csv(VARIANT_SUMMARY_CSV, all_variant_summaries)

    branch_passes = [row for row in branch_summaries if row["hard_gate_result"] == "pass"]
    required_failures = [row for row in branch_summaries if row["hard_gate_result"] != "pass"]
    max_score = max([float(row["rc_spa"]) for row in branch_summaries] or [0.0])
    selected_root_counts = {root: sum(1 for row in selected_rows if row["parent_regime_root"] == root) for root in ROOTS}
    selected_root_counts["Manipulation(scoped)"] = 0
    matrix_root_counts = {root: sum(1 for row in all_variant_rows if row["parent_regime_root"] == root) for root in ROOTS}
    matrix_root_counts["Manipulation(scoped)"] = 0
    if required_failures:
        gate_result = "fail:required_root_branch_hard_gates_failed"
        downstream = "not_started:blocked_by_branch_rc_spa_hard_gates"
        board_state = "rejected"
    else:
        gate_result = "pass:all_required_root_branch_paths_passed"
        downstream = "eligible_for_pre_bayes_bbn_catboost_execution_tree_probe"
        board_state = "research_watch"

    decision = {
        "board_state": board_state,
        "gate_result": gate_result,
        "stable_profit_score": max_score,
        "branch_paths_evaluated": len(branch_summaries),
        "branch_paths_passed": len(branch_passes),
        "required_root_failures": [row["parent_regime_root"] for row in required_failures],
        "selected_trade_rows": len(selected_rows),
        "variant_matrix_trade_rows": len(all_variant_rows),
        "selected_root_trade_counts": selected_root_counts,
        "matrix_root_trade_counts": matrix_root_counts,
        "downstream_consumption": downstream,
        "primary_blocker": (
            "The NQ/Tomac root-aware variant matrix produced real Auto-Quant/Freqtrade rows "
            "and an estimable variant PBO proxy, but at least one required root branch still "
            "failed RC-SPA hard gates; no downstream Pre-Bayes/BBN/CatBoost/execution-tree "
            "promotion is allowed until all required root branches pass with direct rows."
        ),
        "next_action": (
            "B2R-repeat: inspect selected branch failures, then either add a real crisis/direct-event "
            "source panel for scoped Manipulation or synthesize another NQ/root-aware recipe that "
            "improves failing Bear/Sideways/Crisis depth without relaxing RC-SPA gates."
        ),
    }

    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_root": rel(RUN_ROOT),
        "board_b": rel(BOARD_B),
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "accepted_regime_artifact": rel(BOARD_A_CONSUMER_MAP),
        "recipe_id": RECIPE_ID,
        "strategy_class": STRATEGY_CLASS,
        "pair": PAIR,
        "source_ticker": SOURCE_TICKER,
        "auto_quant": {
            "root": str(AUTO_QUANT_ROOT),
            "config": str(AUTO_QUANT_CONFIG),
            "data_path": str(AUTO_QUANT_DATA / "NQ_USD-1h.feather"),
            "generated_strategy_path": rel(STRATEGY_DIR / f"{STRATEGY_CLASS}.py"),
            "variant_matrix": VARIANTS,
            "pinned_ref": git_ref(),
        },
        "rc_spa_parameters": {
            "target_edge": TARGET_EDGE,
            "target_dsr": TARGET_DSR,
            "drawdown_budget": DRAWDOWN_BUDGET,
            "tail_loss_budget": TAIL_LOSS_BUDGET,
            "required_trades": MIN_TOTAL_TRADES,
            "min_test_folds": MIN_TEST_FOLDS,
            "min_trades_per_test_fold": MIN_TRADES_PER_TEST_FOLD,
            "fold_positive_rate_min": FOLD_POSITIVE_RATE_MIN,
            "extra_round_trip_cost_for_2x_fee": EXTRA_ROUND_TRIP_COST_FOR_2X_FEE,
            "pbo_policy": "simple_cscv_proxy_from_same_recipe_parameter_variants",
            "thresholds_relaxed": False,
        },
        "artifacts": {
            "root_schedule": rel(ROOT_SCHEDULE_PATH),
            "selected_trade_rows_csv": rel(TRADES_CSV),
            "variant_branch_rows_csv": rel(VARIANT_ROWS_CSV),
            "branch_summary_csv": rel(SUMMARY_CSV),
            "variant_summary_csv": rel(VARIANT_SUMMARY_CSV),
            "backtest_stdout": rel(backtest_log),
            "backtest_stderr": rel(backtest_err),
        },
        "variant_run_summaries": variant_run_summaries,
        "branch_summaries": branch_summaries,
        "variant_root_summaries": all_variant_summaries,
        "decision": decision,
        "completion": {
            "runtime_code_changed": False,
            "auto_quant_checkout_changed": False,
            "raw_auto_quant_data_committed": False,
            "thresholds_relaxed": False,
            "downstream_runtime_consumed_branch_path": gate_result.startswith("pass:"),
        },
    }
    write_report(report, variant_run_summaries, branch_summaries)

    assertions = [
        f"run_id={RUN_ID}",
        f"recipe_id={RECIPE_ID}",
        f"pair={PAIR}",
        f"variant_count={len(VARIANTS)}",
        f"variant_matrix_trade_rows={len(all_variant_rows)}",
        f"selected_trade_rows={len(selected_rows)}",
        f"gate_result={gate_result}",
        f"stable_profit_score={max_score:.6f}",
        f"branch_paths_passed={len(branch_passes)}",
        f"selected_root_trade_counts={selected_root_counts}",
        f"matrix_root_trade_counts={matrix_root_counts}",
        f"report_json={rel(REPORT_JSON)}",
    ]
    if len(all_variant_rows) == 0:
        assertions.append("ASSERT_FAIL:no_variant_trade_rows")
    if gate_result.startswith("pass:") and not branch_passes:
        assertions.append("ASSERT_FAIL:pass_without_branch_passes")
    ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": not any(line.startswith("ASSERT_FAIL") for line in assertions),
                "run_id": RUN_ID,
                "recipe_id": RECIPE_ID,
                "variant_matrix_trade_rows": len(all_variant_rows),
                "selected_trade_rows": len(selected_rows),
                "stable_profit_score": max_score,
                "gate_result": gate_result,
                "report": rel(REPORT_MD),
            },
            indent=2,
        )
    )
    return 0 if not any(line.startswith("ASSERT_FAIL") for line in assertions) else 1


if __name__ == "__main__":
    raise SystemExit(main())
