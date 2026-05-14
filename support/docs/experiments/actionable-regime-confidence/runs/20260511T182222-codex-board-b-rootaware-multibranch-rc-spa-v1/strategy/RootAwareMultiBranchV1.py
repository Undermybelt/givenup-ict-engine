
from datetime import timedelta
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy


class RootAwareMultiBranchV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.99
    trailing_stop = False
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 250

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
        dataframe["donchian_high_24"] = dataframe["high"].rolling(24).max().shift(1)
        dataframe["volume_sma20"] = dataframe["volume"].rolling(20).mean()
        bb_period = 20
        bb_std = 2.0
        bb_mid = dataframe["close"].rolling(bb_period).mean()
        bb_dev = dataframe["close"].rolling(bb_period).std()
        dataframe["bb_lower"] = bb_mid - bb_std * bb_dev
        dataframe["bb_mid"] = bb_mid
        dataframe["ret_24h"] = dataframe["close"] / dataframe["close"].shift(24) - 1.0
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        bull_volume_mult = self._float_env("BOARD_B_BULL_VOLUME_MULT", 1.10)
        bear_rsi = self._float_env("BOARD_B_BEAR_RSI", 35.0)
        sideways_rsi = self._float_env("BOARD_B_SIDEWAYS_RSI", 42.0)
        crisis_rsi = self._float_env("BOARD_B_CRISIS_RSI", 70.0)

        bull = (
            (dataframe["parent_regime_root"] == "Bull")
            & (dataframe["close"] > dataframe["donchian_high_24"])
            & (dataframe["close"] > dataframe["sma50"])
            & (dataframe["volume"] > bull_volume_mult * dataframe["volume_sma20"])
        )
        bear = (
            (dataframe["parent_regime_root"] == "Bear")
            & (dataframe["rsi"] < bear_rsi)
            & (
                (dataframe["close"] < dataframe["bb_lower"] * 1.01)
                | (dataframe["ret_24h"] < -0.06)
            )
        )
        sideways = (
            (dataframe["parent_regime_root"] == "Sideways")
            & (dataframe["rsi"] < sideways_rsi)
            & (dataframe["close"] < dataframe["bb_mid"])
        )
        crisis = (
            (dataframe["parent_regime_root"] == "Crisis")
            & (dataframe["rsi"] < crisis_rsi)
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[bull | bear | sideways | crisis, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        bull_exit = (
            (dataframe["parent_regime_root"] == "Bull")
            & ((dataframe["close"] < dataframe["ema20"]) | (dataframe["rsi"] > 72))
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
        hold_hours = self._float_env("BOARD_B_HOLD_HOURS", 6.0)
        if current_time - trade.open_date_utc >= timedelta(hours=hold_hours):
            return "rootaware_time_exit"
        return None
