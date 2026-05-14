from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy, informative
from pandas import DataFrame


class TomacNQ_VM_Wide36_AM14_15(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.015

    trailing_stop = True
    trailing_stop_positive = 0.006
    trailing_stop_positive_offset = 0.012
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 260

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=89)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["high_window"] = dataframe["high"].rolling(36).max().shift(1)
        dataframe["low_window"] = dataframe["low"].rolling(36).min().shift(1)
        dataframe["hour_utc"] = dataframe["date"].dt.hour
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        am_killzone = (dataframe["hour_utc"] >= 14) & (dataframe["hour_utc"] <= 15)
        breakout = dataframe["close"] > dataframe["high_window"]
        trend_4h = dataframe["ema_fast_4h"] > dataframe["ema_slow_4h"]
        entry = am_killzone & breakout & trend_4h
        dataframe.loc[entry, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        breakdown = dataframe["close"] < dataframe["low_window"]
        trend_break_4h = dataframe["ema_fast_4h"] < dataframe["ema_slow_4h"]
        dataframe.loc[breakdown | trend_break_4h, "exit_long"] = 1
        return dataframe
