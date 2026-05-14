#!/usr/bin/env python3
"""Board B cross-panel root-aware daily RC-SPA readback.

This additive experiment changes the evidence surface away from repeated
Tomac/NQ-only variants. It uses the local Auto-Quant/Freqtrade runtime with
existing daily feathers, attaches Board A/source-panel roots per instrument,
scores branch-path RC-SPA, and writes fail-closed artifacts under this run root.
It does not modify ict-engine runtime code or the Auto-Quant checkout.
"""

from __future__ import annotations

import contextlib
import csv
import itertools
import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from freqtrade.configuration import Configuration
from freqtrade.enums import RunMode
from freqtrade.optimize.backtesting import Backtesting


RUN_ID = "20260511T190239+0800-codex-board-b-crosspanel-rootaware-daily-v1"
SCHEMA_VERSION = "board-b-crosspanel-rootaware-daily/v1"
RECIPE_ID = "CrossPanelRootAwareDailyV1"
STRATEGY_CLASS = "CrossPanelRootAwareDailyV1"
ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
PAIRS = ["SPY/USD", "QQQ/USD", "NQ/USD", "AAPL/USD", "ES/USD"]
PAIR_SOURCES = {
    "SPY/USD": "^GSPC",
    "QQQ/USD": "^IXIC",
    "NQ/USD": "^IXIC",
    "AAPL/USD": "AAPL",
    "ES/USD": "^GSPC",
}
TIMERANGE = "20110101-20251231"

VARIANTS: list[dict[str, Any]] = [
    {
        "variant_id": "dense_5d",
        "hold_days": 5.0,
        "bull_pullback_pct": 0.018,
        "bull_rsi_high": 78.0,
        "bear_rsi": 42.0,
        "bear_ret_5d": -0.035,
        "sideways_rsi": 45.0,
        "crisis_rsi": 38.0,
        "crisis_ret_5d": -0.070,
    },
    {
        "variant_id": "swing_10d",
        "hold_days": 10.0,
        "bull_pullback_pct": 0.012,
        "bull_rsi_high": 72.0,
        "bear_rsi": 36.0,
        "bear_ret_5d": -0.050,
        "sideways_rsi": 40.0,
        "crisis_rsi": 32.0,
        "crisis_ret_5d": -0.090,
    },
    {
        "variant_id": "broad_rebound_7d",
        "hold_days": 7.0,
        "bull_pullback_pct": 0.025,
        "bull_rsi_high": 82.0,
        "bear_rsi": 48.0,
        "bear_ret_5d": -0.025,
        "sideways_rsi": 50.0,
        "crisis_rsi": 45.0,
        "crisis_ret_5d": -0.055,
    },
    {
        "variant_id": "stress_only_15d",
        "hold_days": 15.0,
        "bull_pullback_pct": 0.010,
        "bull_rsi_high": 70.0,
        "bear_rsi": 30.0,
        "bear_ret_5d": -0.070,
        "sideways_rsi": 35.0,
        "crisis_rsi": 55.0,
        "crisis_ret_5d": -0.030,
    },
    {
        "variant_id": "cost_filtered_3d",
        "hold_days": 3.0,
        "bull_pullback_pct": 0.008,
        "bull_rsi_high": 68.0,
        "bear_rsi": 34.0,
        "bear_ret_5d": -0.055,
        "sideways_rsi": 38.0,
        "crisis_rsi": 34.0,
        "crisis_ret_5d": -0.085,
    },
]

SELECTED_VARIANT_ID = "dense_5d"
TARGET_EDGE = 0.001
TARGET_DSR = 1.0
DRAWDOWN_BUDGET = 0.30
TAIL_LOSS_BUDGET = 0.08
MIN_TOTAL_TRADES = 50
MIN_TEST_FOLDS = 4
MIN_TRADES_PER_TEST_FOLD = 3
FOLD_POSITIVE_RATE_MIN = 0.70
EXTRA_ROUND_TRIP_COST_FOR_2X_COST = 0.001


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
PROVIDER_PANEL_PROBE = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T184121-codex-board-b-crisis-panel-provider-probe-v1/"
    "crisis_panel_provider_probe_v1.md"
)

OUT_DIR = RUN_ROOT / "branch-rc-spa"
CHECK_DIR = RUN_ROOT / "checks"
LOG_DIR = RUN_ROOT / "logs"
STRATEGY_DIR = RUN_ROOT / "strategy"
PROVIDER_DIR = RUN_ROOT / "provider"
ROOT_SCHEDULE_PATH = STRATEGY_DIR / "crosspanel_root_schedule_v1.json"
REPORT_JSON = OUT_DIR / "crosspanel_rootaware_daily_rc_spa_report_v1.json"
REPORT_MD = OUT_DIR / "crosspanel_rootaware_daily_rc_spa_report_v1.md"
TRADE_ROWS_CSV = OUT_DIR / "crosspanel_rootaware_daily_selected_trades_v1.csv"
VARIANT_ROWS_CSV = OUT_DIR / "crosspanel_rootaware_daily_variant_trades_v1.csv"
BRANCH_SUMMARY_CSV = OUT_DIR / "crosspanel_rootaware_daily_branch_summary_v1.csv"
BACKTEST_SUMMARY_CSV = OUT_DIR / "crosspanel_rootaware_daily_backtest_summary_v1.csv"
ASSERTIONS = CHECK_DIR / "crosspanel_rootaware_daily_v1_assertions.out"


STRATEGY_SOURCE = r'''
from datetime import timedelta
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy


class CrossPanelRootAwareDailyV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1d"
    can_short = False
    minimal_roi = {"0": 100}
    stoploss = -0.08
    trailing_stop = False
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 220
    _root_schedule = None

    @classmethod
    def _schedule(cls):
        if cls._root_schedule is None:
            rows = json.loads(Path(os.environ["BOARD_B_CROSSPANEL_ROOT_SCHEDULE"]).read_text(encoding="utf-8"))
            by_pair = {}
            for pair, values in rows.items():
                df = pd.DataFrame(values)
                df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
                by_pair[pair] = df.sort_values("date").reset_index(drop=True)
            cls._root_schedule = by_pair
        return cls._root_schedule

    @staticmethod
    def _float_env(name: str, default: float) -> float:
        try:
            return float(os.environ.get(name, default))
        except (TypeError, ValueError):
            return default

    def _attach_root(self, dataframe: DataFrame, pair: str) -> DataFrame:
        schedule = self._schedule().get(pair)
        if schedule is None or schedule.empty:
            dataframe["parent_regime_root"] = "Unlabeled"
            return dataframe
        context_dates = schedule["date"].values.astype("datetime64[ns]")
        roots = schedule["parent_regime_root"].to_numpy()
        bar_dates = pd.to_datetime(dataframe["date"], utc=True).dt.tz_localize(None)
        bar_dates = bar_dates.dt.normalize().values.astype("datetime64[ns]")
        positions = np.searchsorted(context_dates, bar_dates, side="right") - 1
        labels = np.full(len(dataframe), "Unlabeled", dtype=object)
        valid = positions >= 0
        labels[valid] = roots[positions[valid]]
        dataframe["parent_regime_root"] = labels
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = self._attach_root(dataframe, metadata["pair"])
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema60"] = ta.EMA(dataframe, timeperiod=60)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        bands = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe["bb_upper"] = bands["upperband"]
        dataframe["bb_middle"] = bands["middleband"]
        dataframe["bb_lower"] = bands["lowerband"]
        dataframe["ret_5d"] = dataframe["close"] / dataframe["close"].shift(5) - 1.0
        dataframe["high_20"] = dataframe["high"].rolling(20).max().shift(1)
        dataframe["body_green"] = dataframe["close"] > dataframe["open"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        bull_pullback_pct = self._float_env("BOARD_B_CP_BULL_PULLBACK_PCT", 0.018)
        bull_rsi_high = self._float_env("BOARD_B_CP_BULL_RSI_HIGH", 78.0)
        bear_rsi = self._float_env("BOARD_B_CP_BEAR_RSI", 42.0)
        bear_ret_5d = self._float_env("BOARD_B_CP_BEAR_RET_5D", -0.035)
        sideways_rsi = self._float_env("BOARD_B_CP_SIDEWAYS_RSI", 45.0)
        crisis_rsi = self._float_env("BOARD_B_CP_CRISIS_RSI", 38.0)
        crisis_ret_5d = self._float_env("BOARD_B_CP_CRISIS_RET_5D", -0.070)

        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = None

        bull_long = (
            (dataframe["parent_regime_root"] == "Bull")
            & (dataframe["close"] > dataframe["ema60"])
            & (dataframe["close"] > dataframe["ema200"])
            & (dataframe["rsi"] >= 42)
            & (dataframe["rsi"] <= bull_rsi_high)
            & (dataframe["close"] <= dataframe["ema20"] * (1.0 + bull_pullback_pct))
            & dataframe["body_green"]
        )
        bear_relief = (
            (dataframe["parent_regime_root"] == "Bear")
            & ((dataframe["rsi"] < bear_rsi) | (dataframe["ret_5d"] < bear_ret_5d))
            & dataframe["body_green"]
        )
        sideways_reversion = (
            (dataframe["parent_regime_root"] == "Sideways")
            & ((dataframe["rsi"] < sideways_rsi) | (dataframe["close"] < dataframe["bb_lower"]))
            & (dataframe["close"] > dataframe["ema200"] * 0.70)
        )
        crisis_rebound = (
            (dataframe["parent_regime_root"] == "Crisis")
            & ((dataframe["rsi"] < crisis_rsi) | (dataframe["ret_5d"] < crisis_ret_5d))
            & dataframe["body_green"]
        )
        dataframe.loc[bull_long | bear_relief | sideways_reversion | crisis_rebound, "enter_long"] = 1
        dataframe.loc[bull_long, "enter_tag"] = "Bull/CrossPanelTrendPullback/long"
        dataframe.loc[bear_relief, "enter_tag"] = "Bear/CrossPanelReliefRebound/long"
        dataframe.loc[sideways_reversion, "enter_tag"] = "Sideways/CrossPanelMeanReversion/long"
        dataframe.loc[crisis_rebound, "enter_tag"] = "Crisis/CrossPanelStressRebound/long"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        trend_break = (
            (dataframe["parent_regime_root"] == "Bull")
            & ((dataframe["close"] < dataframe["ema60"]) | (dataframe["rsi"] > 82))
        )
        mean_reversion_done = (
            dataframe["parent_regime_root"].isin(["Bear", "Sideways", "Crisis"])
            & ((dataframe["close"] > dataframe["bb_middle"]) | (dataframe["rsi"] > 58))
        )
        dataframe.loc[trend_break | mean_reversion_done, "exit_long"] = 1
        return dataframe

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        hold_days = self._float_env("BOARD_B_CP_HOLD_DAYS", 5.0)
        if current_time - trade.open_date_utc >= timedelta(days=hold_days):
            return "crosspanel_time_exit"
        return None
'''


BRANCH_MAP = {
    "Bull": {
        "sub_regime_tags": "TrendExpansion",
        "sub_sub_regime_or_profit_factor": "CrossPanelTrendPullback",
        "profit_factor_family": "crosspanel_daily_trend_pullback",
        "allowed_action": "long_research_only_until_branch_rc_spa_passes",
        "suppression_rule": "suppress_if_bull_branch_rc_spa_fails",
    },
    "Bear": {
        "sub_regime_tags": "BearMarketDrawdown",
        "sub_sub_regime_or_profit_factor": "CrossPanelReliefRebound",
        "profit_factor_family": "crosspanel_daily_bear_rebound",
        "allowed_action": "long_research_only_until_branch_rc_spa_passes",
        "suppression_rule": "suppress_if_bear_branch_rc_spa_fails",
    },
    "Sideways": {
        "sub_regime_tags": "RangeConsolidation",
        "sub_sub_regime_or_profit_factor": "CrossPanelMeanReversion",
        "profit_factor_family": "crosspanel_daily_range_reversion",
        "allowed_action": "long_research_only_until_branch_rc_spa_passes",
        "suppression_rule": "suppress_if_sideways_branch_rc_spa_fails",
    },
    "Crisis": {
        "sub_regime_tags": "ExtremeStress",
        "sub_sub_regime_or_profit_factor": "CrossPanelStressRebound",
        "profit_factor_family": "crosspanel_daily_stress_rebound",
        "allowed_action": "long_research_only_until_branch_rc_spa_passes",
        "suppression_rule": "suppress_if_crisis_branch_rc_spa_fails",
    },
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def setup_imports() -> None:
    sys.path.insert(0, str(AUTO_QUANT_ROOT))


def load_tomac_runner():
    setup_imports()
    import run_tomac  # type: ignore

    return run_tomac


def branch_path_for_root(root: str, variant_id: str) -> str:
    if root == "Manipulation(scoped)":
        return "Manipulation(scoped) -> DirectEventOverlayMissing -> no_direct_event_rows -> suppress_or_abstain"
    branch = BRANCH_MAP[root]
    return (
        f"{root} -> {branch['sub_regime_tags']} -> "
        f"{branch['sub_sub_regime_or_profit_factor']} -> {RECIPE_ID}:{variant_id}"
    )


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


def load_root_floors() -> dict[str, float]:
    floors: dict[str, float] = {}
    with BOARD_A_CONSUMER_MAP.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            regime = row["regime"]
            if regime in {"Bull", "Bear", "Sideways", "Crisis", "Manipulation"}:
                floors[regime] = float(row["confidence_floor"])
    return floors


def build_root_schedules() -> dict[str, list[dict[str, Any]]]:
    tickers = sorted(set(PAIR_SOURCES.values()))
    df = pd.read_csv(
        SOURCE_REGIME_CSV,
        usecols=["date", "ticker", "regime_label", "regime_confidence"],
        parse_dates=["date"],
    )
    df = df[df["ticker"].isin(tickers)].copy()
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_localize(None).dt.normalize()
    df["parent_regime_root"] = df["regime_label"].map(lambda item: item if item in ROOTS else "Crisis")
    out: dict[str, list[dict[str, Any]]] = {}
    for pair, source in PAIR_SOURCES.items():
        scoped = df[df["ticker"] == source].sort_values("date")
        out[pair] = [
            {
                "date": pd.Timestamp(row["date"]).date().isoformat(),
                "source_anchor": source,
                "parent_regime_root": str(row["parent_regime_root"]),
                "source_anchor_confidence": float(row["regime_confidence"]),
            }
            for row in scoped.to_dict(orient="records")
        ]
    return out


def write_strategy_and_schedule(schedules: dict[str, list[dict[str, Any]]]) -> None:
    STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
    (STRATEGY_DIR / f"{STRATEGY_CLASS}.py").write_text(STRATEGY_SOURCE, encoding="utf-8")
    write_json(ROOT_SCHEDULE_PATH, schedules)


def apply_variant_env(variant: dict[str, Any]) -> None:
    os.environ["BOARD_B_CROSSPANEL_ROOT_SCHEDULE"] = str(ROOT_SCHEDULE_PATH)
    os.environ["BOARD_B_CP_HOLD_DAYS"] = str(variant["hold_days"])
    os.environ["BOARD_B_CP_BULL_PULLBACK_PCT"] = str(variant["bull_pullback_pct"])
    os.environ["BOARD_B_CP_BULL_RSI_HIGH"] = str(variant["bull_rsi_high"])
    os.environ["BOARD_B_CP_BEAR_RSI"] = str(variant["bear_rsi"])
    os.environ["BOARD_B_CP_BEAR_RET_5D"] = str(variant["bear_ret_5d"])
    os.environ["BOARD_B_CP_SIDEWAYS_RSI"] = str(variant["sideways_rsi"])
    os.environ["BOARD_B_CP_CRISIS_RSI"] = str(variant["crisis_rsi"])
    os.environ["BOARD_B_CP_CRISIS_RET_5D"] = str(variant["crisis_ret_5d"])


def build_config(timerange: str) -> dict[str, Any]:
    base = json.loads(AUTO_QUANT_CONFIG.read_text(encoding="utf-8"))
    base["exchange"]["pair_whitelist"] = PAIRS
    base["exchange"]["skip_pair_validation"] = True
    base["timeframe"] = "1d"
    base["timerange"] = timerange
    base["max_open_trades"] = len(PAIRS)
    base["trading_mode"] = "spot"
    base["fee"] = 0.0
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
    config = build_config(TIMERANGE)
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
        "timerange": TIMERANGE,
        "log_path": rel(log_path),
        "stderr_path": rel(err_path),
        "aggregate_metrics": metrics["aggregate"],
        "per_pair_metrics": metrics["per_pair"],
        "trades": strategy_result.get("trades", []) or [],
    }


class RootLookup:
    def __init__(self, schedules: dict[str, list[dict[str, Any]]]) -> None:
        self.by_pair: dict[str, dict[str, Any]] = {}
        for pair, rows in schedules.items():
            df = pd.DataFrame(rows)
            if df.empty:
                continue
            df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
            self.by_pair[pair] = {
                "dates": df["date"].to_numpy(dtype="datetime64[ns]"),
                "roots": df["parent_regime_root"].to_numpy(),
                "confidence": df["source_anchor_confidence"].to_numpy(),
                "source": df["source_anchor"].to_numpy(),
            }

    def lookup(self, pair: str, value: Any) -> dict[str, Any]:
        item = self.by_pair.get(pair)
        if item is None:
            return {
                "parent_regime_root": "Unlabeled",
                "source_anchor": "",
                "source_anchor_confidence": 0.0,
                "root_lookup_status": "missing_pair_source_schedule",
            }
        date = pd.Timestamp(value).tz_localize(None).normalize().to_datetime64()
        pos = int(np.searchsorted(item["dates"], date, side="right") - 1)
        if pos < 0:
            return {
                "parent_regime_root": "Unlabeled",
                "source_anchor": str(item["source"][0]) if len(item["source"]) else "",
                "source_anchor_confidence": 0.0,
                "root_lookup_status": "missing_before_source_panel",
            }
        return {
            "parent_regime_root": str(item["roots"][pos]),
            "source_anchor": str(item["source"][pos]),
            "source_anchor_confidence": float(item["confidence"][pos]),
            "root_lookup_status": "source_anchor_asof_daily",
        }


def clean_trade(
    trade: dict[str, Any],
    lookup: RootLookup,
    root_floors: dict[str, float],
    variant_id: str,
) -> dict[str, Any]:
    pair = str(trade.get("pair", ""))
    opened = pd.Timestamp(trade["open_date"])
    closed = pd.Timestamp(trade["close_date"])
    root = lookup.lookup(pair, opened)
    parent_root = root["parent_regime_root"]
    if parent_root not in ROOTS:
        parent_root = "Crisis"
    branch = BRANCH_MAP[parent_root]
    profit_ratio = float(trade.get("profit_ratio", 0.0) or 0.0)
    return {
        "run_id": RUN_ID,
        "recipe_id": RECIPE_ID,
        "strategy_class": STRATEGY_CLASS,
        "variant_id": variant_id,
        "pair": pair,
        "source_anchor": root["source_anchor"],
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
        "source_anchor_confidence": root["source_anchor_confidence"],
        "root_lookup_status": root["root_lookup_status"],
        "manipulation_overlay_state": "not_consumed_no_direct_event_rows",
        "sub_regime_tags": branch["sub_regime_tags"],
        "sub_sub_regime_or_profit_factor": branch["sub_sub_regime_or_profit_factor"],
        "profit_factor_family": branch["profit_factor_family"],
        "profit_factor_leaf": f"{RECIPE_ID}:{variant_id}",
        "regime_profit_branch_path": branch_path_for_root(parent_root, variant_id),
        "regime_profit_branch_path_version": SCHEMA_VERSION,
        "trade_or_bar_horizon": "1d_trade",
        "allowed_action": branch["allowed_action"],
        "suppression_rule": branch["suppression_rule"],
        "year_fold": int(opened.year),
        "raw_trade": json.dumps({k: to_jsonable(v) for k, v in trade.items() if k != "orders"}, sort_keys=True),
    }


def bootstrap_lcb(values: np.ndarray, *, seed: int = 190239) -> float:
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
    equity = np.cumprod(1.0 + values)
    peak = np.maximum.accumulate(equity)
    drawdown = equity / peak - 1.0
    return float(abs(drawdown.min())) if len(drawdown) else 0.0


def estimate_pbo(root: str, variant_rows: list[dict[str, Any]]) -> tuple[float, str]:
    scoped = [row for row in variant_rows if row["parent_regime_root"] == root]
    folds = sorted({int(row["year_fold"]) for row in scoped})
    variants = sorted({row["variant_id"] for row in scoped})
    if len(folds) < MIN_TEST_FOLDS or len(variants) < 3:
        return 1.0, "not_identifiable_lt4_folds_or_lt3_variants"
    matrix: dict[str, dict[int, float]] = {}
    for variant in variants:
        matrix[variant] = {}
        for fold in folds:
            vals = [
                float(row["profit_ratio_net"])
                for row in scoped
                if row["variant_id"] == variant and int(row["year_fold"]) == fold
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
    fold_sums = []
    fold_counts = []
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
    specificity_ratio = 999.0 if mean_return > 0.0 and outside_mean <= 0.0 else (
        float(mean_return / outside_mean) if outside_mean > 0.0 else 0.0
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
        "regime_profit_branch_path": branch_path_for_root(root, SELECTED_VARIANT_ID),
        "parent_regime_root": root,
        "total_trades": n,
        "test_folds": len(folds),
        "folds": ",".join(str(fold) for fold in folds),
        "min_trades_per_test_fold": min_trades_per_fold,
        "fold_positive_rate": fold_positive_rate,
        "win_rate": win_rate,
        "mean_profit_ratio_net": mean_return,
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


def write_report(report: dict[str, Any], branch_summaries: list[dict[str, Any]]) -> None:
    decision = report["decision"]
    lines = [
        "# Cross-Panel Root-Aware Daily RC-SPA v1",
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
        f"- Auto-Quant root: `{AUTO_QUANT_ROOT}`",
        f"- Auto-Quant config: `{AUTO_QUANT_CONFIG}`",
        f"- Pairs: `{', '.join(PAIRS)}`",
        f"- Pair source anchors: `{PAIR_SOURCES}`",
        f"- Timerange: `{TIMERANGE}`",
        f"- Provider/panel probe: `{rel(PROVIDER_PANEL_PROBE)}`",
        "",
        "## Variant Backtests",
        "",
        "| Variant | Trades | Win Rate % | Profit % | Sharpe | PF | Log |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["backtest_summaries"]:
        lines.append(
            f"| `{row['variant_id']}` | {row['trade_count']} | {row['win_rate_pct']:.3f} | "
            f"{row['total_profit_pct']:.3f} | {row['sharpe']:.4f} | "
            f"{row['profit_factor']:.3f} | `{row['log_path']}` |"
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
    for row in branch_summaries:
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
            f"- Generated strategy: `{rel(STRATEGY_DIR / (STRATEGY_CLASS + '.py'))}`",
            f"- Root schedule: `{rel(ROOT_SCHEDULE_PATH)}`",
            f"- Selected trade rows: `{rel(TRADE_ROWS_CSV)}`",
            f"- Variant trade rows: `{rel(VARIANT_ROWS_CSV)}`",
            f"- Branch summary: `{rel(BRANCH_SUMMARY_CSV)}`",
            f"- Backtest summary: `{rel(BACKTEST_SUMMARY_CSV)}`",
            f"- Assertions: `{rel(ASSERTIONS)}`",
            "",
            "## Next",
            "",
            f"- {decision['next_action']}",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    for path in [OUT_DIR, CHECK_DIR, LOG_DIR, STRATEGY_DIR, PROVIDER_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    for path in [AUTO_QUANT_CONFIG, SOURCE_REGIME_CSV, BOARD_A_CONSUMER_MAP]:
        if not path.exists():
            raise FileNotFoundError(path)
    missing_data = [pair for pair in PAIRS if not (AUTO_QUANT_DATA / f"{pair.replace('/', '_')}-1d.feather").exists()]
    if missing_data:
        raise FileNotFoundError(f"missing Auto-Quant daily feathers for {missing_data}")

    schedules = build_root_schedules()
    write_strategy_and_schedule(schedules)
    lookup = RootLookup(schedules)
    root_floors = load_root_floors()

    selected_rows: list[dict[str, Any]] = []
    variant_rows: list[dict[str, Any]] = []
    backtest_summaries: list[dict[str, Any]] = []

    for variant in VARIANTS:
        result = run_backtest(variant)
        metrics = result["aggregate_metrics"]
        attached = [
            clean_trade(trade, lookup, root_floors, str(variant["variant_id"]))
            for trade in result["trades"]
        ]
        variant_rows.extend(attached)
        if variant["variant_id"] == SELECTED_VARIANT_ID:
            selected_rows = attached
        backtest_summaries.append(
            {
                "variant_id": variant["variant_id"],
                "timerange": TIMERANGE,
                "trade_count": int(metrics.get("trade_count", 0)),
                "extracted_trade_rows": len(result["trades"]),
                "win_rate_pct": float(metrics.get("win_rate_pct", 0.0)),
                "total_profit_pct": float(metrics.get("total_profit_pct", 0.0)),
                "profit_factor": float(metrics.get("profit_factor", 0.0)),
                "sharpe": float(metrics.get("sharpe", 0.0)),
                "max_drawdown_pct": float(metrics.get("max_drawdown_pct", 0.0)),
                "log_path": result["log_path"],
                "stderr_path": result["stderr_path"],
            }
        )

    write_csv(TRADE_ROWS_CSV, selected_rows)
    write_csv(VARIANT_ROWS_CSV, variant_rows)
    write_csv(BACKTEST_SUMMARY_CSV, backtest_summaries)

    branch_summaries = [summarize_root(root, selected_rows, variant_rows) for root in ROOTS]
    manipulation_summary = {
        "recipe_id": RECIPE_ID,
        "regime_profit_branch_path": branch_path_for_root("Manipulation(scoped)", SELECTED_VARIANT_ID),
        "parent_regime_root": "Manipulation(scoped)",
        "total_trades": 0,
        "test_folds": 0,
        "folds": "",
        "min_trades_per_test_fold": 0,
        "fold_positive_rate": 0.0,
        "win_rate": 0.0,
        "mean_profit_ratio_net": 0.0,
        "bootstrap_edge_lcb_5pct": 0.0,
        "bootstrap_edge_lcb_5pct_stressed_2x_cost": 0.0,
        "pbo": 1.0,
        "pbo_method": "not_identifiable_lt4_folds_or_lt3_variants",
        "dsr": 0.0,
        "dsr_method": "trade_return_sharpe_proxy_not_full_deflated_sharpe",
        "cost_stress_result": "fail",
        "tail_loss_p95": 0.0,
        "max_drawdown_trade_equity_proxy": 0.0,
        "regime_specificity_ratio": 0.0,
        "outside_mean_profit_ratio_net": float(np.mean([float(row["profit_ratio_net"]) for row in selected_rows])) if selected_rows else 0.0,
        "rc_spa": 10.0,
        "promotion_level": "reject",
        "hard_gate_result": "fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60",
        "downstream_consumption_status": "not_started:blocked_by_branch_rc_spa_hard_gates",
    }
    branch_summaries.append(manipulation_summary)
    write_csv(BRANCH_SUMMARY_CSV, branch_summaries)

    passed = [row for row in branch_summaries if row["hard_gate_result"] == "pass"]
    root_counts = {row["parent_regime_root"]: int(row["total_trades"]) for row in branch_summaries}
    score = max((float(row["rc_spa"]) for row in branch_summaries), default=0.0)
    gate_result = "pass" if len(passed) == len(branch_summaries) else "fail:all_branch_paths_failed_rc_spa_hard_gates"
    downstream = (
        "eligible_for_pre_bayes_bbn_catboost_execution_tree"
        if gate_result == "pass"
        else "not_started:blocked_by_branch_rc_spa_hard_gates"
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "recipe_id": RECIPE_ID,
        "strategy_class": STRATEGY_CLASS,
        "pairs": PAIRS,
        "pair_sources": PAIR_SOURCES,
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "accepted_regime_artifact": rel(BOARD_A_CONSUMER_MAP),
        "provider_panel_probe": rel(PROVIDER_PANEL_PROBE),
        "decision": {
            "board_state": "rejected" if gate_result != "pass" else "stable_candidate",
            "gate_result": gate_result,
            "stable_profit_score": score,
            "selected_trade_rows": len(selected_rows),
            "variant_trade_rows": len(variant_rows),
            "branch_paths_evaluated": len(branch_summaries),
            "branch_paths_passed": len(passed),
            "root_trade_counts": root_counts,
            "downstream_consumption": downstream,
            "primary_blocker": (
                "Cross-panel daily Auto-Quant/Freqtrade readback changed the source/panel surface, "
                "but at least one required root branch still failed RC-SPA hard gates; scoped "
                "Manipulation remains zero direct rows."
            ),
            "next_action": (
                "B2R-repeat: do not promote downstream; acquire real direct Manipulation rows "
                "or move to a different non-Tomac family with explicit provider/panel change."
            ),
        },
        "backtest_summaries": backtest_summaries,
        "branch_summaries": branch_summaries,
        "artifacts": {
            "report_json": rel(REPORT_JSON),
            "report_md": rel(REPORT_MD),
            "selected_trade_rows_csv": rel(TRADE_ROWS_CSV),
            "variant_trade_rows_csv": rel(VARIANT_ROWS_CSV),
            "branch_summary_csv": rel(BRANCH_SUMMARY_CSV),
            "backtest_summary_csv": rel(BACKTEST_SUMMARY_CSV),
            "root_schedule": rel(ROOT_SCHEDULE_PATH),
            "generated_strategy": rel(STRATEGY_DIR / f"{STRATEGY_CLASS}.py"),
            "assertions": rel(ASSERTIONS),
        },
        "completion": {
            "runtime_code_changed": False,
            "auto_quant_checkout_changed": False,
            "raw_auto_quant_data_committed": False,
            "thresholds_relaxed_after_scoring": False,
            "downstream_runtime_consumed_branch_path": gate_result == "pass",
        },
    }
    write_json(REPORT_JSON, report)
    write_report(report, branch_summaries)

    assertions = [
        f"run_id={RUN_ID}",
        f"recipe_id={RECIPE_ID}",
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
    if not selected_rows:
        assertions.append("ASSERT_FAIL selected_trade_rows_zero")
    missing_roots = [root for root in ROOTS if root_counts.get(root, 0) == 0]
    if missing_roots:
        assertions.append(f"candidate_failure_missing_required_roots={missing_roots}")
    ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
