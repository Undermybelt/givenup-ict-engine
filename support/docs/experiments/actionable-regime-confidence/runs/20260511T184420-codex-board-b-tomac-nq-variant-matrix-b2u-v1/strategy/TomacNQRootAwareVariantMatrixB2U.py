
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
