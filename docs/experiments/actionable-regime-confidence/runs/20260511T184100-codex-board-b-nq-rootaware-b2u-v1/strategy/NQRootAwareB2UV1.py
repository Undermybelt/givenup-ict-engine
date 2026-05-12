
from datetime import timedelta
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy


class NQRootAwareB2UV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1d"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.20
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
            schedule_path = Path(os.environ["BOARD_B_ROOT_SCHEDULE"])
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
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["sma50"] = ta.SMA(dataframe, timeperiod=50)
        dataframe["sma200"] = ta.SMA(dataframe, timeperiod=200)
        dataframe["donchian_high_10"] = dataframe["high"].rolling(10).max().shift(1)
        dataframe["donchian_high_15"] = dataframe["high"].rolling(15).max().shift(1)
        dataframe["donchian_high_20"] = dataframe["high"].rolling(20).max().shift(1)
        dataframe["donchian_high_50"] = dataframe["high"].rolling(50).max().shift(1)
        bb_period = 20
        bb_std = 2.0
        bb_mid = dataframe["close"].rolling(bb_period).mean()
        bb_dev = dataframe["close"].rolling(bb_period).std()
        dataframe["bb_lower"] = bb_mid - bb_std * bb_dev
        dataframe["bb_mid"] = bb_mid
        dataframe["ret_5d"] = dataframe["close"] / dataframe["close"].shift(5) - 1.0
        dataframe["ret_20d"] = dataframe["close"] / dataframe["close"].shift(20) - 1.0
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        bull_breakout = int(self._float_env("BOARD_B_BULL_BREAKOUT", 20.0))
        bear_rsi = self._float_env("BOARD_B_BEAR_RSI", 28.0)
        sideways_rsi = self._float_env("BOARD_B_SIDEWAYS_RSI", 38.0)
        crisis_rsi = self._float_env("BOARD_B_CRISIS_RSI", 24.0)
        breakout_col = f"donchian_high_{bull_breakout}"

        bull = (
            (dataframe["parent_regime_root"] == "Bull")
            & (dataframe["close"] > dataframe[breakout_col])
            & (dataframe["sma50"] > dataframe["sma200"])
        )
        bear = (
            (dataframe["parent_regime_root"] == "Bear")
            & (dataframe["rsi"] < bear_rsi)
            & (
                (dataframe["close"] < dataframe["bb_lower"] * 1.02)
                | (dataframe["ret_20d"] < -0.12)
            )
        )
        sideways = (
            (dataframe["parent_regime_root"] == "Sideways")
            & (dataframe["rsi"] < sideways_rsi)
            & (dataframe["close"] < dataframe["bb_lower"] * 1.03)
        )
        crisis = (
            (dataframe["parent_regime_root"] == "Crisis")
            & (dataframe["rsi"] < crisis_rsi)
            & ((dataframe["close"] < dataframe["bb_lower"]) | (dataframe["ret_5d"] < -0.08))
        )
        dataframe.loc[bull | bear | sideways | crisis, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        bull_exit = (
            (dataframe["parent_regime_root"] == "Bull")
            & ((dataframe["close"] < dataframe["ema20"]) | (dataframe["rsi"] > 76))
        )
        mr_exit = (
            dataframe["parent_regime_root"].isin(["Bear", "Sideways"])
            & ((dataframe["close"] > dataframe["bb_mid"]) | (dataframe["rsi"] > 55))
        )
        crisis_exit = (
            (dataframe["parent_regime_root"] == "Crisis")
            & ((dataframe["rsi"] > 50) | (dataframe["close"] > dataframe["ema20"]))
        )
        dataframe.loc[bull_exit | mr_exit | crisis_exit, "exit_long"] = 1
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
        hold_days = self._float_env("BOARD_B_HOLD_DAYS", 12.0)
        if current_time - trade.open_date_utc >= timedelta(days=hold_days):
            return "rootaware_time_exit"
        return None
