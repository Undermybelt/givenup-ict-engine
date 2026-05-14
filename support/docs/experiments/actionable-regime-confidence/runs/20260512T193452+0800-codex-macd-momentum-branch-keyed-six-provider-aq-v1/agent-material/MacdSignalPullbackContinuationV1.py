from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class MacdSignalPullbackContinuationV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 100}
    stoploss = -0.045
    trailing_stop = True
    trailing_stop_positive = 0.012
    trailing_stop_positive_offset = 0.026
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count: int = 240

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema55"] = ta.EMA(dataframe, timeperiod=55)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        trend = (dataframe["close"] > dataframe["ema55"]) & (dataframe["ema21"] > dataframe["ema55"])
        signal_reclaim = (dataframe["macd"] > dataframe["macdsignal"]) & (dataframe["macd"].shift(1) <= dataframe["macdsignal"].shift(1))
        pullback_zone = (dataframe["macd"] > 0) & dataframe["rsi"].between(40, 68)
        entry = trend & signal_reclaim & pullback_zone
        dataframe.loc[entry, "enter_long"] = 1
        dataframe.loc[entry, "enter_tag"] = "macd_signal_pullback_continuation_v1"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        exit_signal = (dataframe["macd"] < 0) | (dataframe["close"] < dataframe["ema55"]) | (dataframe["rsi"] > 80)
        dataframe.loc[exit_signal, "exit_long"] = 1
        return dataframe
