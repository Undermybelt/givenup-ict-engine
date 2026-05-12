from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class OteRetrace0705ContinuationV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.030
    trailing_stop = True
    trailing_stop_positive = 0.011
    trailing_stop_positive_offset = 0.024
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count: int = 260

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["swing_high_48"] = dataframe["high"].rolling(48, min_periods=24).max().shift(1)
        dataframe["swing_low_48"] = dataframe["low"].rolling(48, min_periods=24).min().shift(1)
        dataframe["impulse_range_48"] = dataframe["swing_high_48"] - dataframe["swing_low_48"]
        dataframe["ote_price"] = dataframe["swing_high_48"] - dataframe["impulse_range_48"] * 0.705
        dataframe["ote_touch"] = dataframe["low"] <= dataframe["ote_price"]
        dataframe["ote_reclaim"] = dataframe["close"] > dataframe["ote_price"]
        dataframe["hour_utc"] = dataframe["date"].dt.hour
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""

        trend_expansion = (
            (dataframe["ema20"] > dataframe["ema50"])
            & (dataframe["ema50"] > dataframe["ema200"])
            & (dataframe["close"] > dataframe["ema200"])
            & (dataframe["impulse_range_48"] > dataframe["atr"] * 2.8)
        )
        pullback_continuation = (
            trend_expansion
            & dataframe["ote_touch"]
            & dataframe["ote_reclaim"]
            & (dataframe["rsi"].between(38, 68))
            & dataframe["hour_utc"].between(0, 23)
        )

        dataframe.loc[pullback_continuation, "enter_long"] = 1
        dataframe.loc[pullback_continuation, "enter_tag"] = "ote_retrace_0705_continuation_v1"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        trend_loss = dataframe["close"] < dataframe["ema50"]
        exhaustion = dataframe["rsi"] > 76
        failed_reclaim = dataframe["close"] < dataframe["ote_price"] - dataframe["atr"] * 0.35
        dataframe.loc[trend_loss | exhaustion | failed_reclaim, "exit_long"] = 1
        return dataframe
