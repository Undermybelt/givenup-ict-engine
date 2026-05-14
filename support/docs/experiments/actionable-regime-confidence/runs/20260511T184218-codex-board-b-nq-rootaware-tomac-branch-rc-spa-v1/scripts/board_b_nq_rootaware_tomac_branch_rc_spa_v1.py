#!/usr/bin/env python3
"""Board B NQ root-aware Tomac-style branch RC-SPA evidence builder.

This is an additive experiment artifact. It uses the local Auto-Quant
Freqtrade runtime plus existing NQ/USD feather data, writes generated strategy
and scoring artifacts under this run root, and does not modify ict-engine
runtime code or the Auto-Quant checkout.
"""

from __future__ import annotations

import csv
import itertools
import json
import math
import os
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from freqtrade.configuration import Configuration
from freqtrade.enums import RunMode
from freqtrade.optimize.backtesting import Backtesting
from freqtrade.resolvers import ExchangeResolver


RUN_ID = "20260511T184218+0800-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1"
SCHEMA_VERSION = "board-b-nq-rootaware-tomac-branch-rc-spa/v1"
RECIPE_ID = "TomacNQRootAwareBranchMatrixV1"
STRATEGY_CLASS = "TomacNQRootAwareBranchMatrixV1"
PAIR = "NQ/USD"
TIMERANGE = "20110101-20251231"

VARIANTS = [
    {
        "variant_id": "baseline_4h",
        "hold_hours": 4.0,
        "bull_pullback_pct": 0.008,
        "bull_rsi_high": 75.0,
        "bear_rsi_low": 25.0,
        "bear_rsi_high": 62.0,
        "sideways_rsi_low": 40.0,
        "crisis_rsi": 55.0,
    },
    {
        "variant_id": "dense_2h",
        "hold_hours": 2.0,
        "bull_pullback_pct": 0.012,
        "bull_rsi_high": 78.0,
        "bear_rsi_low": 20.0,
        "bear_rsi_high": 68.0,
        "sideways_rsi_low": 45.0,
        "crisis_rsi": 65.0,
    },
    {
        "variant_id": "swing_8h",
        "hold_hours": 8.0,
        "bull_pullback_pct": 0.006,
        "bull_rsi_high": 72.0,
        "bear_rsi_low": 28.0,
        "bear_rsi_high": 58.0,
        "sideways_rsi_low": 35.0,
        "crisis_rsi": 45.0,
    },
    {
        "variant_id": "wide_16h",
        "hold_hours": 16.0,
        "bull_pullback_pct": 0.020,
        "bull_rsi_high": 82.0,
        "bear_rsi_low": 18.0,
        "bear_rsi_high": 72.0,
        "sideways_rsi_low": 50.0,
        "crisis_rsi": 90.0,
    },
]

TARGET_EDGE = 0.001
TARGET_DSR = 1.0
DRAWDOWN_BUDGET = 0.25
TAIL_LOSS_BUDGET = 0.03
NQ_INTRADAY_REQUIRED_TRADES = 100
MIN_TEST_FOLDS = 4
MIN_TRADES_PER_TEST_FOLD = 10
FOLD_POSITIVE_RATE_MIN = 0.75
EXTRA_ROUND_TRIP_COST_FOR_2X_COST = 0.0002


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot find repo root from {start}")


RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = find_repo_root(Path(__file__).resolve())
AUTO_QUANT_ROOT = Path(os.environ.get("AUTO_QUANT_ROOT", "/Users/thrill3r/Auto-Quant"))
AUTO_QUANT_CONFIG = AUTO_QUANT_ROOT / "config.tomac.json"
AUTO_QUANT_DATA = AUTO_QUANT_ROOT / "user_data" / "data"
AUTO_QUANT_USER_DATA = AUTO_QUANT_ROOT / "user_data"
LOCAL_FUTURES_DATA = Path(
    os.environ.get(
        "BOARD_B_NQ_FUTURES_DATA_DIR",
        "/tmp/ict-engine-board-b-nq-rootaware-tomac-data-20260511T184218",
    )
)
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
BOARD_A_NQ_ATTACHMENT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T170714-codex-qqq-nq-daily-crossmarket-attachment-v1/"
    "crossmarket-attachment/qqq_nq_daily_crossmarket_attachment_v1.md"
)

OUT_DIR = RUN_ROOT / "branch-rc-spa"
CHECK_DIR = RUN_ROOT / "checks"
LOG_DIR = RUN_ROOT / "logs"
STRATEGY_DIR = RUN_ROOT / "strategy"
ROOT_SCHEDULE_PATH = STRATEGY_DIR / "nq_ixic_root_schedule_v1.json"

REPORT_JSON = OUT_DIR / "nq_rootaware_tomac_branch_rc_spa_report_v1.json"
REPORT_MD = OUT_DIR / "nq_rootaware_tomac_branch_rc_spa_report_v1.md"
TRADE_ROWS_CSV = OUT_DIR / "nq_rootaware_tomac_branch_path_trades_v1.csv"
VARIANT_ROWS_CSV = OUT_DIR / "nq_rootaware_tomac_variant_branch_rows_v1.csv"
BRANCH_SUMMARY_CSV = OUT_DIR / "nq_rootaware_tomac_branch_rc_spa_summary_v1.csv"
BACKTEST_SUMMARY_CSV = OUT_DIR / "nq_rootaware_tomac_backtest_summaries_v1.csv"
ASSERTIONS = CHECK_DIR / "nq_rootaware_tomac_branch_rc_spa_v1_assertions.out"


BRANCH_MAP = {
    "Bull": {
        "sub_regime_tags": "TrendExpansion",
        "sub_sub_regime_or_profit_factor": "TomacNQTrendPullbackContinuation",
        "profit_factor_family": "tomac_nq_root_aware_trend_pullback",
        "profit_factor_leaf": RECIPE_ID,
        "allowed_action": "long_research_only_until_branch_rc_spa_passes",
        "suppression_rule": "suppress_if_bull_branch_rc_spa_fails",
    },
    "Bear": {
        "sub_regime_tags": "BearMarketDrawdown",
        "sub_sub_regime_or_profit_factor": "TomacNQBearTrendShortContinuation",
        "profit_factor_family": "tomac_nq_root_aware_bear_short",
        "profit_factor_leaf": RECIPE_ID,
        "allowed_action": "short_research_only_until_branch_rc_spa_passes",
        "suppression_rule": "suppress_if_bear_branch_rc_spa_fails",
    },
    "Sideways": {
        "sub_regime_tags": "RangeConsolidation",
        "sub_sub_regime_or_profit_factor": "TomacNQRangeLowerBreakContinuation",
        "profit_factor_family": "tomac_nq_root_aware_sideways_short_mean_break",
        "profit_factor_leaf": RECIPE_ID,
        "allowed_action": "short_research_only_until_branch_rc_spa_passes",
        "suppression_rule": "suppress_if_sideways_branch_rc_spa_fails",
    },
    "Crisis": {
        "sub_regime_tags": "ExtremeStress",
        "sub_sub_regime_or_profit_factor": "TomacNQStressReboundLong",
        "profit_factor_family": "tomac_nq_root_aware_crisis_rebound",
        "profit_factor_leaf": RECIPE_ID,
        "allowed_action": "long_research_only_until_branch_rc_spa_passes",
        "suppression_rule": "suppress_if_crisis_branch_rc_spa_fails",
    },
}


def branch_path_for_root(root: str) -> str:
    branch = BRANCH_MAP[root]
    return (
        f"{root} -> {branch['sub_regime_tags']} -> "
        f"{branch['sub_sub_regime_or_profit_factor']} -> "
        f"{branch['profit_factor_leaf']}"
    )


REQUIRED_ROOT_PATHS = [branch_path_for_root(root) for root in ["Bull", "Bear", "Sideways", "Crisis"]]
MANIPULATION_PATH = (
    "Manipulation(scoped) -> DirectEventOverlayMissing -> "
    "no_direct_event_rows -> suppress_or_abstain"
)


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


class TomacNQRootAwareBranchMatrixV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = True

    minimal_roi = {"0": 100}
    stoploss = -0.04
    trailing_stop = False
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 200

    _root_schedule = None

    @classmethod
    def _schedule(cls):
        if cls._root_schedule is None:
            schedule_path = Path(os.environ["BOARD_B_NQ_ROOT_SCHEDULE"])
            rows = json.loads(schedule_path.read_text(encoding="utf-8"))
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
        bar_dates = pd.to_datetime(dataframe["date"], utc=True).dt.tz_localize(None)
        bar_dates = bar_dates.dt.normalize().values.astype("datetime64[ns]")
        positions = np.searchsorted(context_dates, bar_dates, side="right") - 1
        labels = np.full(len(dataframe), "Unlabeled", dtype=object)
        valid = positions >= 0
        labels[valid] = roots[positions[valid]]
        dataframe["parent_regime_root"] = labels
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = self._attach_root(dataframe)
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema89"] = ta.EMA(dataframe, timeperiod=89)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        bands = ta.BBANDS(dataframe, timeperiod=24, nbdevup=2.0, nbdevdn=2.0)
        dataframe["bb_upper"] = bands["upperband"]
        dataframe["bb_middle"] = bands["middleband"]
        dataframe["bb_lower"] = bands["lowerband"]
        dataframe["high_12"] = dataframe["high"].rolling(6).max().shift(1)
        dataframe["low_12"] = dataframe["low"].rolling(6).min().shift(1)
        dataframe["ret_1d"] = dataframe["close"] / dataframe["close"].shift(24) - 1.0
        dataframe["hour_utc"] = dataframe["date"].dt.hour
        dataframe["body_green"] = dataframe["close"] > dataframe["open"]
        dataframe["body_red"] = dataframe["close"] < dataframe["open"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        bull_pullback_pct = self._float_env("BOARD_B_NQ_BULL_PULLBACK_PCT", 0.008)
        bull_rsi_high = self._float_env("BOARD_B_NQ_BULL_RSI_HIGH", 75.0)
        bear_rsi_low = self._float_env("BOARD_B_NQ_BEAR_RSI_LOW", 25.0)
        bear_rsi_high = self._float_env("BOARD_B_NQ_BEAR_RSI_HIGH", 62.0)
        sideways_rsi_low = self._float_env("BOARD_B_NQ_SIDEWAYS_RSI_LOW", 40.0)
        crisis_rsi = self._float_env("BOARD_B_NQ_CRISIS_RSI", 55.0)

        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        dataframe["enter_tag"] = None

        liquid_window = (dataframe["hour_utc"] >= 8) & (dataframe["hour_utc"] <= 22)
        bull_long = (
            (dataframe["parent_regime_root"] == "Bull")
            & liquid_window
            & (dataframe["close"] > dataframe["ema89"])
            & ((dataframe["ema21"] > dataframe["ema89"]) | (dataframe["close"] > dataframe["high_12"]))
            & (dataframe["rsi"] >= 38)
            & (dataframe["rsi"] <= bull_rsi_high)
            & (dataframe["close"] <= dataframe["ema21"] * (1.0 + bull_pullback_pct))
            & dataframe["body_green"]
        )
        bear_short = (
            (dataframe["parent_regime_root"] == "Bear")
            & liquid_window
            & (dataframe["close"] < dataframe["ema89"])
            & ((dataframe["ema21"] < dataframe["ema89"]) | (dataframe["close"] < dataframe["low_12"]))
            & (dataframe["rsi"] >= bear_rsi_low)
            & (dataframe["rsi"] <= bear_rsi_high)
            & dataframe["body_red"]
        )
        sideways_short = (
            (dataframe["parent_regime_root"] == "Sideways")
            & liquid_window
            & ((dataframe["rsi"] < sideways_rsi_low) | (dataframe["close"] < dataframe["bb_lower"]))
            & dataframe["body_red"]
        )
        crisis_long = (
            (dataframe["parent_regime_root"] == "Crisis")
            & liquid_window
            & ((dataframe["rsi"] < crisis_rsi) | (dataframe["ret_1d"] < -0.02))
        )

        dataframe.loc[bull_long | crisis_long, "enter_long"] = 1
        dataframe.loc[bear_short | sideways_short, "enter_short"] = 1
        dataframe.loc[bull_long, "enter_tag"] = "Bull/TomacNQTrendPullbackContinuation/long"
        dataframe.loc[bear_short, "enter_tag"] = "Bear/TomacNQBearTrendShortContinuation/short"
        dataframe.loc[sideways_short, "enter_tag"] = "Sideways/TomacNQRangeLowerBreakContinuation/short"
        dataframe.loc[crisis_long, "enter_tag"] = "Crisis/TomacNQStressReboundLong/long"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        bull_or_crisis_break = (
            dataframe["parent_regime_root"].isin(["Bull", "Crisis"])
            & ((dataframe["close"] < dataframe["ema89"] * 0.985) | (dataframe["rsi"] > 82))
        )
        short_reversal = (
            dataframe["parent_regime_root"].isin(["Bear", "Sideways"])
            & ((dataframe["close"] > dataframe["ema21"] * 1.012) | (dataframe["rsi"] > 58))
        )
        dataframe.loc[bull_or_crisis_break, "exit_long"] = 1
        dataframe.loc[short_reversal, "exit_short"] = 1
        return dataframe

    def custom_exit(
        self,
        pair: str,
        trade,
        current_time,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ):
        hold_hours = self._float_env("BOARD_B_NQ_HOLD_HOURS", 4.0)
        if current_time - trade.open_date_utc >= timedelta(hours=hold_hours):
            return "nq_rootaware_time_exit"
        return None
'''


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


def synthetic_market(pair: str, trading_mode: str) -> dict[str, Any]:
    base, quote = pair.split("/", 1)
    is_futures = trading_mode == "futures"
    return {
        "id": pair.replace("/", ""),
        "symbol": pair,
        "base": base,
        "quote": quote,
        "active": True,
        "type": "swap" if is_futures else "spot",
        "spot": not is_futures,
        "margin": is_futures,
        "swap": is_futures,
        "future": False,
        "option": False,
        "contract": is_futures,
        "linear": True if is_futures else None,
        "inverse": False if is_futures else None,
        "settle": quote if is_futures else None,
        "settleId": quote if is_futures else None,
        "expiry": None,
        "expiryDatetime": None,
        "strike": None,
        "optionType": None,
        "taker": 0.0,
        "maker": 0.0,
        "percentage": True,
        "tierBased": False,
        "feeSide": "get",
        "precision": {"amount": 8, "price": 8, "base": 8, "quote": 8},
        "limits": {
            "amount": {"min": 0, "max": None},
            "price": {"min": 0, "max": None},
            "cost": {"min": 0, "max": None},
            "leverage": {"min": 1, "max": 20 if is_futures else 1},
        },
        "info": {},
    }


def build_exchange_with_synthetic_pair(config: dict[str, Any]):
    exchange = ExchangeResolver.load_exchange(
        config,
        validate=False,
        load_leverage_tiers=False,
    )
    if exchange._api.markets is None:
        exchange._api.markets = {}
    if exchange._api_async.markets is None:
        exchange._api_async.markets = {}
    market = synthetic_market(PAIR, config.get("trading_mode", "spot"))
    exchange._markets[PAIR] = market
    exchange._api.markets[PAIR] = market
    exchange._api_async.markets[PAIR] = market
    exchange._leverage_tiers[PAIR] = [
        {
            "minNotional": 0.0,
            "maxNotional": 1_000_000_000.0,
            "maintenanceMarginRate": 0.005,
            "maxLeverage": 1.0,
            "maintAmt": 0.0,
        }
    ]
    return exchange


def prepare_futures_datadir() -> Path:
    """Expose existing NQ 1h candles to Freqtrade's futures filename convention.

    The source feather stays in Auto-Quant. The experiment creates only a /tmp
    symlink so the repo does not absorb raw market data.
    """
    source = AUTO_QUANT_DATA / "NQ_USD-1h.feather"
    futures_dir = LOCAL_FUTURES_DATA / "futures"
    futures_dir.mkdir(parents=True, exist_ok=True)
    target = futures_dir / "NQ_USD-1h-futures.feather"
    if target.exists() or target.is_symlink():
        target.unlink()
    target.symlink_to(source)
    return LOCAL_FUTURES_DATA


def load_root_floors() -> dict[str, float]:
    floors: dict[str, float] = {}
    with BOARD_A_CONSUMER_MAP.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            regime = row["regime"]
            if regime in {"Bull", "Bear", "Sideways", "Crisis", "Manipulation"}:
                floors[regime] = float(row["confidence_floor"])
    return floors


def build_nq_root_schedule() -> pd.DataFrame:
    df = pd.read_csv(
        SOURCE_REGIME_CSV,
        usecols=["date", "ticker", "regime_label", "regime_confidence", "vix"],
    )
    df = df[df["ticker"] == "^IXIC"].copy()
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.normalize()
    df = df.sort_values("date").reset_index(drop=True)
    df = df.rename(
        columns={
            "regime_label": "parent_regime_root",
            "regime_confidence": "source_anchor_confidence",
        }
    )
    return df[
        ["date", "parent_regime_root", "source_anchor_confidence", "vix"]
    ].reset_index(drop=True)


def write_strategy_and_schedule(schedule: pd.DataFrame) -> None:
    STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
    (STRATEGY_DIR / f"{STRATEGY_CLASS}.py").write_text(STRATEGY_SOURCE, encoding="utf-8")
    rows = []
    for row in schedule.to_dict(orient="records"):
        rows.append(
            {
                "date": pd.Timestamp(row["date"]).date().isoformat(),
                "parent_regime_root": str(row["parent_regime_root"]),
                "source_anchor": "^IXIC",
                "target": "NQ=F",
                "source_anchor_confidence": float(row["source_anchor_confidence"]),
                "vix": float(row["vix"]),
            }
        )
    write_json(ROOT_SCHEDULE_PATH, rows)


def apply_variant_env(variant: dict[str, Any]) -> None:
    os.environ["BOARD_B_NQ_ROOT_SCHEDULE"] = str(ROOT_SCHEDULE_PATH)
    os.environ["BOARD_B_NQ_HOLD_HOURS"] = str(variant["hold_hours"])
    os.environ["BOARD_B_NQ_BULL_PULLBACK_PCT"] = str(variant["bull_pullback_pct"])
    os.environ["BOARD_B_NQ_BULL_RSI_HIGH"] = str(variant["bull_rsi_high"])
    os.environ["BOARD_B_NQ_BEAR_RSI_LOW"] = str(variant["bear_rsi_low"])
    os.environ["BOARD_B_NQ_BEAR_RSI_HIGH"] = str(variant["bear_rsi_high"])
    os.environ["BOARD_B_NQ_SIDEWAYS_RSI_LOW"] = str(variant["sideways_rsi_low"])
    os.environ["BOARD_B_NQ_CRISIS_RSI"] = str(variant["crisis_rsi"])


def run_backtest(variant: dict[str, Any]) -> dict[str, Any]:
    apply_variant_env(variant)
    datadir = prepare_futures_datadir()
    args = {
        "config": [str(AUTO_QUANT_CONFIG)],
        "user_data_dir": str(AUTO_QUANT_USER_DATA),
        "datadir": str(datadir),
        "strategy": STRATEGY_CLASS,
        "strategy_path": str(STRATEGY_DIR),
        "timerange": TIMERANGE,
        "export": "none",
        "exportfilename": None,
        "cache": "none",
    }
    config = Configuration(args, RunMode.BACKTEST).get_config()
    config["exchange"]["pair_whitelist"] = [PAIR]
    config["timeframe"] = "1h"
    config["trading_mode"] = "futures"
    config["margin_mode"] = "isolated"
    config["max_open_trades"] = 1
    config["fee"] = 0.0
    exchange = build_exchange_with_synthetic_pair(config)
    bt = Backtesting(config, exchange=exchange)
    bt.start()
    return bt.results


def strategy_result(results: dict[str, Any]) -> dict[str, Any]:
    return results.get("strategy", {}).get(STRATEGY_CLASS, {}) or {}


def metric(result: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        value = result.get(key)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                pass
    return default


def extract_trades(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for trade in result.get("trades", []) or []:
        rows.append({k: to_jsonable(v) for k, v in trade.items() if k != "orders"})
    return rows


def attach_root_context(
    trades: list[dict[str, Any]],
    schedule: pd.DataFrame,
    root_floors: dict[str, float],
    variant_id: str,
) -> list[dict[str, Any]]:
    context_dates = list(schedule["date"])
    attached: list[dict[str, Any]] = []
    for idx, trade in enumerate(trades, start=1):
        open_value = trade.get("open_date") or trade.get("open_date_utc")
        opened = pd.to_datetime(open_value, utc=True)
        trade_date = opened.normalize()
        pos = np.searchsorted(context_dates, trade_date, side="right") - 1
        if pos < 0:
            root = "Unlabeled"
            source_date = ""
            source_confidence = 0.0
            source_vix = 0.0
            attachment_policy = "missing_source_context"
        else:
            ctx = schedule.iloc[int(pos)]
            root = str(ctx["parent_regime_root"])
            source_date = pd.Timestamp(ctx["date"]).date().isoformat()
            source_confidence = float(ctx["source_anchor_confidence"])
            source_vix = float(ctx["vix"])
            attachment_policy = "^IXIC_source_anchor_previous_session_context_asof_NQ_daily_attachment"
        branch = BRANCH_MAP.get(root, {})
        branch_path = (
            f"{root} -> {branch.get('sub_regime_tags', 'Unlabeled')} -> "
            f"{branch.get('sub_sub_regime_or_profit_factor', 'Unlabeled')} -> "
            f"{branch.get('profit_factor_leaf', RECIPE_ID)}"
        )
        is_short = str(trade.get("is_short", "False")).lower() == "true"
        profit_ratio = float(trade.get("profit_ratio") or 0.0)
        attached.append(
            {
                "row_id": idx,
                "variant_id": variant_id,
                "recipe_id": RECIPE_ID,
                "strategy_class": STRATEGY_CLASS,
                "pair": trade.get("pair", PAIR),
                "side": "short" if is_short else "long",
                "open_date": pd.Timestamp(opened).isoformat(),
                "close_date": to_jsonable(trade.get("close_date", "")),
                "open_session_date": trade_date.date().isoformat(),
                "source_regime_session_date": source_date,
                "source_context_attachment_policy": attachment_policy,
                "source_anchor": "^IXIC",
                "target_market": "NQ=F/NQ_USD",
                "parent_regime_root": root,
                "parent_regime_confidence_floor": root_floors.get(root, 0.0),
                "source_anchor_confidence": source_confidence,
                "source_anchor_vix": source_vix,
                "manipulation_overlay_state": "not_consumed_no_direct_event_rows",
                "sub_regime_tags": branch.get("sub_regime_tags", "Unlabeled"),
                "sub_sub_regime_or_profit_factor": branch.get(
                    "sub_sub_regime_or_profit_factor", "Unlabeled"
                ),
                "profit_factor_family": branch.get("profit_factor_family", "tomac_nq_root_aware"),
                "profit_factor_leaf": branch.get("profit_factor_leaf", RECIPE_ID),
                "regime_profit_branch_path": branch_path,
                "regime_profit_branch_path_version": SCHEMA_VERSION,
                "trade_or_bar_horizon": "1h_trade",
                "allowed_action": branch.get("allowed_action", "research_only"),
                "suppression_rule": branch.get("suppression_rule", "suppress_until_labeled"),
                "year_fold": int(pd.Timestamp(opened).year),
                "profit_ratio_net": profit_ratio,
                "profit_abs": float(trade.get("profit_abs") or 0.0),
                "stake_amount": float(trade.get("stake_amount") or 0.0),
                "leverage": float(trade.get("leverage") or 1.0),
                "fee_open": float(trade.get("fee_open") or 0.0),
                "fee_close": float(trade.get("fee_close") or 0.0),
                "enter_tag": trade.get("enter_tag", ""),
                "exit_reason": trade.get("exit_reason", ""),
                "is_open": bool(trade.get("is_open", False)),
            }
        )
    return attached


def bootstrap_lcb(values: np.ndarray, seed: int = 42) -> float:
    if len(values) == 0:
        return 0.0
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(5000, len(values)), replace=True)
    means = draws.mean(axis=1)
    return float(np.quantile(means, 0.05))


def max_drawdown_from_returns(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    equity = np.cumprod(1.0 + values)
    peak = np.maximum.accumulate(equity)
    drawdown = equity / peak - 1.0
    return float(abs(drawdown.min()))


def estimate_pbo(path: str, variant_rows: list[dict[str, Any]]) -> tuple[float, str]:
    folds = sorted({int(r["year_fold"]) for r in variant_rows if r["regime_profit_branch_path"] == path})
    variants = sorted({r["variant_id"] for r in variant_rows if r["regime_profit_branch_path"] == path})
    if len(folds) < MIN_TEST_FOLDS or len(variants) < 3:
        return 1.0, "not_identifiable_lt4_folds_or_lt3_variants"
    matrix: dict[str, dict[int, float]] = {variant: {} for variant in variants}
    for variant in variants:
        for fold in folds:
            vals = [
                float(r["profit_ratio_net"])
                for r in variant_rows
                if r["variant_id"] == variant
                and r["regime_profit_branch_path"] == path
                and int(r["year_fold"]) == fold
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
        train_scores = {
            variant: float(np.mean([matrix[variant][fold] for fold in train]))
            for variant in variants
        }
        winner = max(train_scores.items(), key=lambda item: item[1])[0]
        test_scores = {
            variant: float(np.mean([matrix[variant][fold] for fold in test]))
            for variant in variants
        }
        median_test = float(np.median(list(test_scores.values())))
        if test_scores[winner] < median_test:
            overfit += 1
    return float(overfit / len(splits)), "simple_cscv_variant_fold_proxy"


def summarize_branch(
    path: str,
    rows: list[dict[str, Any]],
    selected_rows: list[dict[str, Any]],
    variant_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    returns = np.array([float(r["profit_ratio_net"]) for r in rows], dtype=float)
    outside = np.array(
        [float(r["profit_ratio_net"]) for r in selected_rows if r["regime_profit_branch_path"] != path],
        dtype=float,
    )
    n = int(len(returns))
    folds = sorted({int(r["year_fold"]) for r in rows})
    fold_sums = []
    fold_counts = []
    for fold in folds:
        vals = np.array(
            [float(r["profit_ratio_net"]) for r in rows if int(r["year_fold"]) == fold],
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
    branch_mdd = max_drawdown_from_returns(returns)
    outside_mean = float(outside.mean()) if len(outside) else 0.0
    if mean_return > 0.0 and outside_mean <= 0.0:
        specificity_ratio = 999.0
    elif outside_mean > 0.0:
        specificity_ratio = float(mean_return / outside_mean)
    else:
        specificity_ratio = 0.0
    fold_positive_rate = (
        float(sum(1 for value in fold_sums if value > 0.0) / len(fold_sums))
        if fold_sums
        else 0.0
    )
    min_trades_per_fold = int(min(fold_counts)) if fold_counts else 0
    pbo, pbo_method = estimate_pbo(path, variant_rows)

    edge_score = min(max(bootstrap_edge_lcb / TARGET_EDGE, 0.0), 1.0)
    fold_score = fold_positive_rate
    depth_score = min(max(n / NQ_INTRADAY_REQUIRED_TRADES, 0.0), 1.0)
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

    failures = []
    if n < NQ_INTRADAY_REQUIRED_TRADES:
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

    parent_root = rows[0]["parent_regime_root"] if rows else path.split(" -> ", 1)[0]
    return {
        "recipe_id": RECIPE_ID,
        "regime_profit_branch_path": path,
        "parent_regime_root": parent_root,
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
        "max_drawdown_trade_equity_proxy": branch_mdd,
        "regime_specificity_ratio": specificity_ratio,
        "outside_mean_profit_ratio_net": outside_mean,
        "rc_spa": rc_spa,
        "promotion_level": "reject" if failures else ("research_watch" if rc_spa < 75 else "stable_candidate"),
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
        "# NQ Root-Aware Tomac Branch RC-SPA v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Stable profit score: `{decision['stable_profit_score']:.4f}`",
        f"- Branch paths evaluated: `{decision['branch_paths_evaluated']}`",
        f"- Branch paths passed: `{decision['branch_paths_passed']}`",
        f"- Required root failures: `{', '.join(decision['required_root_failures']) if decision['required_root_failures'] else 'none'}`",
        f"- Root trade counts: `{decision['root_trade_counts']}`",
        f"- Downstream consumption: `{decision['downstream_consumption']}`",
        f"- Primary blocker: {decision['primary_blocker']}",
        "",
        "## Inputs",
        "",
        f"- Auto-Quant root: `{AUTO_QUANT_ROOT}`",
        f"- Auto-Quant config: `{AUTO_QUANT_CONFIG}`",
        f"- Pair: `{PAIR}`",
        f"- Timerange: `{TIMERANGE}`",
        f"- Board A consumer map: `{rel(BOARD_A_CONSUMER_MAP)}`",
        f"- Board A NQ attachment: `{rel(BOARD_A_NQ_ATTACHMENT)}`",
        f"- Source anchor: `^IXIC`; target: `NQ=F`; local data: `NQ_USD-1h.feather`",
        "",
        "## Variant Backtests",
        "",
        "| Variant | Trades | Win Rate | Profit % | Sharpe | Drawdown % | Log |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["backtest_summaries"]:
        lines.append(
            f"| `{row['variant_id']}` | {row['trade_count']} | {row['win_rate']:.4f} | "
            f"{row['total_profit_pct']:.4f} | {row['sharpe']:.4f} | "
            f"{row['max_drawdown_pct']:.4f} | `{row['log_path']}` |"
        )
    lines.extend(
        [
            "",
            "## Branch Summary",
            "",
            "| Root | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in branch_summaries:
        lines.append(
            f"| {row['parent_regime_root']} | {row['total_trades']} | {row['test_folds']} | "
            f"{row['min_trades_per_test_fold']} | {row['fold_positive_rate']:.4f} | "
            f"{row['bootstrap_edge_lcb_5pct']:.6f} | {row['pbo']:.2f} | "
            f"{row['dsr']:.4f} | {row['rc_spa']:.4f} | `{row['hard_gate_result']}` |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Report JSON: `{rel(REPORT_JSON)}`",
            f"- Generated strategy: `{rel(STRATEGY_DIR / (STRATEGY_CLASS + '.py'))}`",
            f"- Root schedule: `{rel(ROOT_SCHEDULE_PATH)}`",
            f"- Trade rows: `{rel(TRADE_ROWS_CSV)}`",
            f"- Variant branch rows: `{rel(VARIANT_ROWS_CSV)}`",
            f"- Branch summary: `{rel(BRANCH_SUMMARY_CSV)}`",
            f"- Backtest summary: `{rel(BACKTEST_SUMMARY_CSV)}`",
            "",
            "## Next",
            "",
            f"- {decision['next_action']}",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    for path in [OUT_DIR, CHECK_DIR, LOG_DIR, STRATEGY_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    if not AUTO_QUANT_CONFIG.exists():
        raise FileNotFoundError(AUTO_QUANT_CONFIG)
    if not (AUTO_QUANT_DATA / "NQ_USD-1h.feather").exists():
        raise FileNotFoundError(AUTO_QUANT_DATA / "NQ_USD-1h.feather")
    if not SOURCE_REGIME_CSV.exists():
        raise FileNotFoundError(SOURCE_REGIME_CSV)
    if not BOARD_A_CONSUMER_MAP.exists():
        raise FileNotFoundError(BOARD_A_CONSUMER_MAP)

    schedule = build_nq_root_schedule()
    root_floors = load_root_floors()
    write_strategy_and_schedule(schedule)

    selected_variant = VARIANTS[0]
    selected_rows: list[dict[str, Any]] = []
    variant_rows: list[dict[str, Any]] = []
    backtest_summaries: list[dict[str, Any]] = []

    for variant in VARIANTS:
        log_path = LOG_DIR / f"freqtrade_backtest_{variant['variant_id']}.out"
        err_path = LOG_DIR / f"freqtrade_backtest_{variant['variant_id']}.err"
        with log_path.open("w", encoding="utf-8") as out, err_path.open("w", encoding="utf-8") as err:
            with redirect_stdout(out), redirect_stderr(err):
                results = run_backtest(variant)
        result = strategy_result(results)
        trades = extract_trades(result)
        attached = attach_root_context(trades, schedule, root_floors, str(variant["variant_id"]))
        variant_rows.extend(attached)
        if variant["variant_id"] == selected_variant["variant_id"]:
            selected_rows = attached
        backtest_summaries.append(
            {
                "variant_id": variant["variant_id"],
                "timerange": TIMERANGE,
                "trade_count": int(metric(result, "total_trades", "trades")),
                "extracted_trade_rows": len(trades),
                "win_rate": metric(result, "winrate"),
                "total_profit_pct": metric(result, "profit_total") * 100.0,
                "profit_factor": metric(result, "profit_factor"),
                "sharpe": metric(result, "sharpe"),
                "max_drawdown_pct": -abs(metric(result, "max_drawdown_account")) * 100.0,
                "log_path": rel(log_path),
                "err_path": rel(err_path),
            }
        )

    write_csv(TRADE_ROWS_CSV, selected_rows)
    write_csv(VARIANT_ROWS_CSV, variant_rows)
    write_csv(BACKTEST_SUMMARY_CSV, backtest_summaries)

    observed_paths = sorted({row["regime_profit_branch_path"] for row in selected_rows})
    paths_to_score = list(dict.fromkeys([*REQUIRED_ROOT_PATHS, MANIPULATION_PATH, *observed_paths]))
    branch_summaries = []
    for path in paths_to_score:
        rows = [row for row in selected_rows if row["regime_profit_branch_path"] == path]
        branch_summaries.append(summarize_branch(path, rows, selected_rows, variant_rows))
    write_csv(BRANCH_SUMMARY_CSV, branch_summaries)

    branch_passes = [item for item in branch_summaries if item["hard_gate_result"] == "pass"]
    required_root_failures = [
        item
        for item in branch_summaries
        if item["regime_profit_branch_path"] in REQUIRED_ROOT_PATHS
        and item["hard_gate_result"] != "pass"
    ]
    max_rc_spa = max([float(item["rc_spa"]) for item in branch_summaries] or [0.0])
    root_counts = {
        root: sum(1 for row in selected_rows if row["parent_regime_root"] == root)
        for root in ["Bull", "Bear", "Sideways", "Crisis"]
    }
    source_counts = (
        schedule[
            (schedule["date"] >= pd.Timestamp("2011-01-01", tz="UTC"))
            & (schedule["date"] <= pd.Timestamp("2025-12-31", tz="UTC"))
        ]["parent_regime_root"]
        .value_counts()
        .to_dict()
    )

    if not branch_passes:
        gate_result = "fail:all_branch_paths_failed_rc_spa_hard_gates"
        downstream = "not_started:blocked_by_branch_rc_spa_hard_gates"
        board_state = "rejected"
    elif required_root_failures:
        gate_result = "fail:required_root_branch_hard_gates_failed"
        downstream = "not_started:blocked_by_required_root_branch_failures"
        board_state = "rejected"
    else:
        gate_result = "pass:all_required_root_branch_paths_passed"
        downstream = "eligible_for_pre_bayes_bbn_catboost_execution_tree_probe"
        board_state = "research_watch"

    decision = {
        "board_state": board_state,
        "gate_result": gate_result,
        "stable_profit_score": max_rc_spa,
        "branch_paths_evaluated": len(branch_summaries),
        "branch_paths_passed": len(branch_passes),
        "required_root_failures": [item["parent_regime_root"] for item in required_root_failures],
        "total_trade_rows": len(selected_rows),
        "root_trade_counts": root_counts,
        "source_anchor_root_day_counts_2011_2025": source_counts,
        "downstream_consumption": downstream,
        "primary_blocker": (
            "TomacNQRootAwareBranchMatrixV1 uses the accepted ^IXIC-to-NQ daily root attachment "
            "and real local Auto-Quant/Freqtrade NQ 1h data, but downstream promotion is allowed "
            "only if every required root branch clears RC-SPA hard gates."
        ),
        "next_action": (
            "B2R-repeat: keep NQ/Tomac evidence only if branch gates improve; otherwise broaden "
            "root/source labels or synthesize another root-aware recipe before downstream promotion."
        ),
    }

    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_root": rel(RUN_ROOT),
        "recipe_id": RECIPE_ID,
        "strategy_class": STRATEGY_CLASS,
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "accepted_regime_artifact": rel(BOARD_A_CONSUMER_MAP),
        "board_a_nq_attachment_artifact": rel(BOARD_A_NQ_ATTACHMENT),
        "auto_quant": {
            "root": str(AUTO_QUANT_ROOT),
            "config": str(AUTO_QUANT_CONFIG),
            "data_file": str(AUTO_QUANT_DATA / "NQ_USD-1h.feather"),
            "freqtrade_futures_datadir": str(LOCAL_FUTURES_DATA),
            "pair": PAIR,
            "timerange": TIMERANGE,
            "variant_matrix": VARIANTS,
            "generated_strategy_path": rel(STRATEGY_DIR / f"{STRATEGY_CLASS}.py"),
        },
        "rc_spa_parameters": {
            "target_edge": TARGET_EDGE,
            "target_dsr": TARGET_DSR,
            "drawdown_budget": DRAWDOWN_BUDGET,
            "tail_loss_budget": TAIL_LOSS_BUDGET,
            "required_trades": NQ_INTRADAY_REQUIRED_TRADES,
            "min_test_folds": MIN_TEST_FOLDS,
            "min_trades_per_test_fold": MIN_TRADES_PER_TEST_FOLD,
            "fold_positive_rate_min": FOLD_POSITIVE_RATE_MIN,
            "extra_round_trip_cost_for_2x_cost": EXTRA_ROUND_TRIP_COST_FOR_2X_COST,
            "pbo_policy": "simple_cscv_proxy_from_same_recipe_parameter_variants",
        },
        "artifacts": {
            "report_md": rel(REPORT_MD),
            "report_json": rel(REPORT_JSON),
            "trade_rows_csv": rel(TRADE_ROWS_CSV),
            "variant_rows_csv": rel(VARIANT_ROWS_CSV),
            "branch_summary_csv": rel(BRANCH_SUMMARY_CSV),
            "backtest_summary_csv": rel(BACKTEST_SUMMARY_CSV),
            "root_schedule": rel(ROOT_SCHEDULE_PATH),
        },
        "backtest_summaries": backtest_summaries,
        "branch_summaries": branch_summaries,
        "decision": decision,
        "completion": {
            "runtime_code_changed": False,
            "auto_quant_checkout_changed": False,
            "raw_auto_quant_data_committed": False,
            "thresholds_relaxed_after_scoring": False,
            "downstream_runtime_consumed_branch_path": gate_result.startswith("pass:"),
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
        f"branch_paths_passed={len(branch_passes)}",
        f"gate_result={gate_result}",
        f"downstream_consumption={downstream}",
        f"report_json={rel(REPORT_JSON)}",
        f"report_md={rel(REPORT_MD)}",
    ]
    if len(selected_rows) <= 0:
        assertions.append("ASSERT_FAIL:no_selected_variant_trade_rows")
    if any(root_counts[root] <= 0 for root in ["Bull", "Bear", "Sideways", "Crisis"]):
        assertions.append("ASSERT_FAIL:missing_required_root_trade_rows")
    ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": not any(line.startswith("ASSERT_FAIL") for line in assertions),
                "run_id": RUN_ID,
                "recipe_id": RECIPE_ID,
                "selected_trade_rows": len(selected_rows),
                "root_counts": root_counts,
                "rc_spa": max_rc_spa,
                "gate_result": gate_result,
                "downstream_consumption": downstream,
                "report": rel(REPORT_MD),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 1 if any(line.startswith("ASSERT_FAIL") for line in assertions) else 0


if __name__ == "__main__":
    raise SystemExit(main())
