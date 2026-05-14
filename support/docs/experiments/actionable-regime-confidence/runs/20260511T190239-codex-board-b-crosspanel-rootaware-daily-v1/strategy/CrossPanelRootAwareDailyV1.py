
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
