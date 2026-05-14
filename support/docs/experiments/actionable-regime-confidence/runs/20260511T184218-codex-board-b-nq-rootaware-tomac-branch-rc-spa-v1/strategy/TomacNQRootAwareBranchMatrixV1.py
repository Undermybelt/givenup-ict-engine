
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
