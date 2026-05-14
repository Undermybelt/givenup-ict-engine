from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class ProviderBackedTrendPullbackResume1h(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.045

    trailing_stop = True
    trailing_stop_positive = 0.010
    trailing_stop_positive_offset = 0.025
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 260

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema100"] = ta.EMA(dataframe, timeperiod=100)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["atr_pct_med120"] = dataframe["atr_pct"].rolling(120).median()
        dataframe["pullback_depth"] = (dataframe["ema20"] - dataframe["low"]) / dataframe["atr"]
        dataframe["momentum_3h"] = dataframe["close"].pct_change(3)
        dataframe["range_expansion"] = (dataframe["high"] - dataframe["low"]) / dataframe["atr"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        trend_expansion = (
            (dataframe["close"] > dataframe["ema100"])
            & (dataframe["ema50"] > dataframe["ema200"])
            & (dataframe["ema20"] > dataframe["ema50"])
        )
        normal_volatility = (
            (dataframe["atr_pct"] > dataframe["atr_pct_med120"] * 0.55)
            & (dataframe["atr_pct"] < dataframe["atr_pct_med120"] * 1.65)
        )
        down_or_flat_pullback = (
            (dataframe["momentum_3h"] <= 0.004)
            | (dataframe["low"].shift(1) <= dataframe["ema20"].shift(1))
        )
        resume_trigger = (
            (dataframe["close"] > dataframe["ema20"])
            & (dataframe["close"] > dataframe["close"].shift(1))
            & (dataframe["rsi"].between(43, 68))
            & (dataframe["pullback_depth"].between(-0.35, 2.75))
            & (dataframe["range_expansion"] >= 0.45)
        )
        dataframe.loc[
            trend_expansion & normal_volatility & down_or_flat_pullback & resume_trigger,
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        trend_break = dataframe["close"] < dataframe["ema50"]
        momentum_exhaustion = dataframe["rsi"] > 78
        volatility_break = dataframe["atr_pct"] > dataframe["atr_pct_med120"] * 2.4
        dataframe.loc[trend_break | momentum_exhaustion | volatility_break, "exit_long"] = 1
        return dataframe
