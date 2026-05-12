from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class OtePullbackContinuationLongV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.034
    trailing_stop = True
    trailing_stop_positive = 0.010
    trailing_stop_positive_offset = 0.026
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

        swing_high = dataframe["high"].rolling(48, min_periods=24).max().shift(1)
        swing_low = dataframe["low"].rolling(48, min_periods=24).min().shift(1)
        leg = (swing_high - swing_low).clip(lower=0)
        dataframe["ote_0500"] = swing_high - leg * 0.500
        dataframe["ote_0618"] = swing_high - leg * 0.618
        dataframe["ote_0705"] = swing_high - leg * 0.705
        dataframe["ote_0786"] = swing_high - leg * 0.786
        dataframe["trend_ok"] = (
            (dataframe["ema20"] > dataframe["ema50"])
            & (dataframe["ema50"] > dataframe["ema200"])
            & (dataframe["close"] > dataframe["ema200"])
        )
        dataframe["impulse_ok"] = swing_high > swing_high.shift(24)
        return dataframe

    def _entry_for_level(self, dataframe: DataFrame, level: str) -> DataFrame:
        target = dataframe[level]
        touched = (dataframe["low"] <= target) & (dataframe["high"] >= target)
        reclaimed = dataframe["close"] > target
        momentum = dataframe["rsi"].between(42, 68)
        volatility = dataframe["atr"] > dataframe["atr"].rolling(48, min_periods=16).median()
        return dataframe["trend_ok"] & dataframe["impulse_ok"] & touched & reclaimed & momentum & volatility

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""

        for level, tag in [
            ("ote_0500", "ote_retrace_0500_continuation_v1"),
            ("ote_0618", "ote_retrace_0618_continuation_v1"),
            ("ote_0705", "ote_retrace_0705_continuation_v1"),
            ("ote_0786", "ote_retrace_0786_continuation_v1"),
        ]:
            mask = self._entry_for_level(dataframe, level)
            dataframe.loc[mask, "enter_long"] = 1
            dataframe.loc[mask, "enter_tag"] = tag
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        trend_loss = dataframe["close"] < dataframe["ema50"]
        overextended = dataframe["rsi"] > 76
        atr_break = dataframe["close"] < (dataframe["ema20"] - dataframe["atr"] * 1.7)
        dataframe.loc[trend_loss | overextended | atr_break, "exit_long"] = 1
        return dataframe
