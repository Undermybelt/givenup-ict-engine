from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class BoardAProviderBreadthProbeV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.035

    trailing_stop = True
    trailing_stop_positive = 0.012
    trailing_stop_positive_offset = 0.028
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 80

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema55"] = ta.EMA(dataframe, timeperiod=55)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["hour_utc"] = dataframe["date"].dt.hour
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        trend_ok = dataframe["ema21"] > dataframe["ema55"]
        momentum_ok = (dataframe["rsi"] >= 42) & (dataframe["rsi"] <= 68)
        candle_ok = dataframe["close"] > dataframe["open"]
        volatility_ok = (dataframe["atr"] / dataframe["close"]) <= 0.045
        all_hours = (dataframe["hour_utc"] >= 0) & (dataframe["hour_utc"] <= 23)
        entry = trend_ok & momentum_ok & candle_ok & volatility_ok & all_hours
        dataframe.loc[entry, "enter_long"] = 1
        dataframe.loc[entry, "enter_tag"] = "board_a_provider_breadth_probe_v1"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        exit_signal = (dataframe["close"] < dataframe["ema21"]) | (dataframe["rsi"] > 76)
        dataframe.loc[exit_signal, "exit_long"] = 1
        return dataframe
