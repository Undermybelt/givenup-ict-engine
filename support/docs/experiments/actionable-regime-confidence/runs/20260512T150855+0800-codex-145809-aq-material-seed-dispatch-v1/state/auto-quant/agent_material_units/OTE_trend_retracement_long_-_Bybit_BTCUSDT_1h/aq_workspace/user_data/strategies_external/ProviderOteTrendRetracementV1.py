from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class ProviderOteTrendRetracementV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.035

    trailing_stop = True
    trailing_stop_positive = 0.010
    trailing_stop_positive_offset = 0.024
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 260

    ote_levels = [
        ("ote_050", 0.500),
        ("ote_0618", 0.618),
        ("ote_0705", 0.705),
        ("ote_0786", 0.786),
    ]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["swing_low"] = dataframe["low"].rolling(120, min_periods=60).min()
        dataframe["swing_high"] = dataframe["high"].rolling(120, min_periods=60).max()
        dataframe["impulse"] = dataframe["swing_high"] - dataframe["swing_low"]
        dataframe["impulse_atr"] = dataframe["impulse"] / dataframe["atr"]
        dataframe["hour_utc"] = dataframe["date"].dt.hour
        dataframe["prior_low_lookback"] = dataframe["low"].rolling(12, min_periods=3).min().shift(1)
        dataframe["recovering"] = dataframe["close"] > dataframe["open"]
        dataframe["higher_time_proxy_trend"] = (dataframe["ema50"] > dataframe["ema200"]) & (
            dataframe["close"] > dataframe["ema200"]
        )
        for tag, level in self.ote_levels:
            price = dataframe["swing_high"] - (dataframe["impulse"] * level)
            dataframe[f"{tag}_price"] = price
            dataframe[f"{tag}_touch"] = (
                (dataframe["low"] <= price + dataframe["atr"] * 0.20)
                & (dataframe["close"] >= price - dataframe["atr"] * 0.05)
            )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""

        liquid_window = (dataframe["hour_utc"] >= 0) & (dataframe["hour_utc"] <= 23)
        trend_ok = dataframe["higher_time_proxy_trend"]
        impulse_ok = dataframe["impulse_atr"] >= 3.0
        not_exhausted = (dataframe["rsi"] >= 34) & (dataframe["rsi"] <= 68)
        reclaim = dataframe["recovering"] & (dataframe["close"] > dataframe["prior_low_lookback"])

        for tag, _level in self.ote_levels:
            mask = (
                liquid_window
                & trend_ok
                & impulse_ok
                & not_exhausted
                & reclaim
                & dataframe[f"{tag}_touch"]
            )
            dataframe.loc[mask, "enter_long"] = 1
            dataframe.loc[mask, "enter_tag"] = tag
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        trend_break = dataframe["close"] < dataframe["ema50"]
        local_exhaustion = dataframe["rsi"] > 78
        swing_target = dataframe["close"] >= (dataframe["swing_high"] - dataframe["atr"] * 0.15)
        dataframe.loc[trend_break | local_exhaustion | swing_target, "exit_long"] = 1
        return dataframe
