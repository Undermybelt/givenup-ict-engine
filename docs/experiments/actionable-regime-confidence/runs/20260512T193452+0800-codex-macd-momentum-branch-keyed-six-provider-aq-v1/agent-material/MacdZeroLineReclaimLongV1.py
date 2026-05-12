from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class MacdZeroLineReclaimLongV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 100}
    stoploss = -0.040
    trailing_stop = True
    trailing_stop_positive = 0.010
    trailing_stop_positive_offset = 0.022
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count: int = 240

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema34"] = ta.EMA(dataframe, timeperiod=34)
        dataframe["ema89"] = ta.EMA(dataframe, timeperiod=89)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        trend = (dataframe["close"] > dataframe["ema34"]) & (dataframe["ema34"] > dataframe["ema89"])
        zero_reclaim = (dataframe["macd"] > 0) & (dataframe["macd"].shift(1) <= 0)
        momentum_ok = dataframe["rsi"].between(44, 72) & (dataframe["macdhist"] > dataframe["macdhist"].shift(1))
        entry = trend & zero_reclaim & momentum_ok
        dataframe.loc[entry, "enter_long"] = 1
        dataframe.loc[entry, "enter_tag"] = "macd_zero_line_reclaim_long_v1"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        exit_signal = (dataframe["macd"] < dataframe["macdsignal"]) | (dataframe["close"] < dataframe["ema34"]) | (dataframe["rsi"] > 78)
        dataframe.loc[exit_signal, "exit_long"] = 1
        return dataframe
