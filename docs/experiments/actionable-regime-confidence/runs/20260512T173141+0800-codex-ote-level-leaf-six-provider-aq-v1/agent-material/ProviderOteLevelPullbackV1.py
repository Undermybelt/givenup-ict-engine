from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class ProviderOteLevelPullbackV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.032

    trailing_stop = True
    trailing_stop_positive = 0.012
    trailing_stop_positive_offset = 0.026
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 240

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["hour_utc"] = dataframe["date"].dt.hour

        dataframe["swing_high"] = dataframe["high"].rolling(96, min_periods=48).max().shift(1)
        dataframe["swing_low"] = dataframe["low"].rolling(96, min_periods=48).min().shift(1)
        impulse = (dataframe["swing_high"] - dataframe["swing_low"]).clip(lower=0)
        dataframe["ote_050"] = dataframe["swing_high"] - impulse * 0.500
        dataframe["ote_0618"] = dataframe["swing_high"] - impulse * 0.618
        dataframe["ote_0705"] = dataframe["swing_high"] - impulse * 0.705
        dataframe["ote_0786"] = dataframe["swing_high"] - impulse * 0.786

        dataframe["trend_expansion_normal_vol"] = (
            (dataframe["ema21"] > dataframe["ema50"])
            & (dataframe["close"] > dataframe["ema200"])
            & (dataframe["close"] > dataframe["swing_low"])
            & ((dataframe["atr"] / dataframe["close"]) >= 0.002)
            & ((dataframe["atr"] / dataframe["close"]) <= 0.050)
            & (dataframe["rsi"] >= 34)
            & (dataframe["rsi"] <= 68)
        )
        return dataframe

    def _ote_touch(self, dataframe: DataFrame, level_column: str):
        tolerance = dataframe["atr"] * 0.10
        return (
            dataframe[level_column].notna()
            & (dataframe["low"] <= dataframe[level_column] + tolerance)
            & (dataframe["close"] >= dataframe[level_column] - tolerance)
            & (dataframe["close"] > dataframe["open"])
        )

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""

        liquid_window = (dataframe["hour_utc"] >= 0) & (dataframe["hour_utc"] <= 23)
        base = liquid_window & dataframe["trend_expansion_normal_vol"]

        leaves = [
            ("ote_0786", "ote_pullback_0786_v1"),
            ("ote_0705", "ote_pullback_0705_v1"),
            ("ote_0618", "ote_pullback_0618_v1"),
            ("ote_050", "ote_pullback_050_v1"),
        ]
        for column, tag in leaves:
            condition = base & self._ote_touch(dataframe, column)
            dataframe.loc[condition, "enter_long"] = 1
            dataframe.loc[condition, "enter_tag"] = tag
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        trend_break = dataframe["close"] < dataframe["ema50"]
        local_exhaustion = dataframe["rsi"] > 74
        volatility_break = (dataframe["atr"] / dataframe["close"]) > 0.060
        dataframe.loc[trend_break | local_exhaustion | volatility_break, "exit_long"] = 1
        return dataframe
