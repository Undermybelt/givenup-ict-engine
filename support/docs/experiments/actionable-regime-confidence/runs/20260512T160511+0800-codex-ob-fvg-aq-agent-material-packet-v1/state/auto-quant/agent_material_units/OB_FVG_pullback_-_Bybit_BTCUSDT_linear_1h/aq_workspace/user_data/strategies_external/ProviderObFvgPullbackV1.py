from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class ProviderObFvgPullbackV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.030

    trailing_stop = True
    trailing_stop_positive = 0.010
    trailing_stop_positive_offset = 0.022
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 260

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["hour_utc"] = dataframe["date"].dt.hour

        displacement_up = dataframe["close"] > (dataframe["high"].shift(1) + dataframe["atr"] * 0.20)
        prior_bear = dataframe["close"].shift(1) < dataframe["open"].shift(1)
        ob_seed = displacement_up & prior_bear
        ob_low = dataframe["close"].shift(1).where(ob_seed)
        ob_high = dataframe["open"].shift(1).where(ob_seed)
        dataframe["ob_low"] = ob_low.ffill().shift(1)
        dataframe["ob_high"] = ob_high.ffill().shift(1)

        fvg_seed = dataframe["low"] > (dataframe["high"].shift(2) + dataframe["atr"] * 0.08)
        fvg_low = dataframe["high"].shift(2).where(fvg_seed)
        fvg_high = dataframe["low"].where(fvg_seed)
        dataframe["fvg_low"] = fvg_low.ffill().shift(1)
        dataframe["fvg_high"] = fvg_high.ffill().shift(1)

        dataframe["trend_transition_low_vol_up"] = (
            (dataframe["ema21"] > dataframe["ema50"])
            & (dataframe["close"] > dataframe["ema50"])
            & (dataframe["atr"] / dataframe["close"] < 0.020)
            & (dataframe["rsi"] >= 38)
            & (dataframe["rsi"] <= 66)
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""

        liquid_window = (dataframe["hour_utc"] >= 0) & (dataframe["hour_utc"] <= 23)
        reclaim = dataframe["close"] > dataframe["open"]
        ob_touch = (
            dataframe["ob_low"].notna()
            & (dataframe["low"] <= dataframe["ob_high"] + dataframe["atr"] * 0.10)
            & (dataframe["close"] >= dataframe["ob_low"])
        )
        fvg_touch = (
            dataframe["fvg_low"].notna()
            & (dataframe["low"] <= dataframe["fvg_high"] + dataframe["atr"] * 0.10)
            & (dataframe["close"] >= dataframe["fvg_low"])
        )
        base = liquid_window & dataframe["trend_transition_low_vol_up"] & reclaim

        dataframe.loc[base & fvg_touch, "enter_long"] = 1
        dataframe.loc[base & fvg_touch, "enter_tag"] = "fair_value_gap_pullback_v1"
        dataframe.loc[base & ob_touch, "enter_long"] = 1
        dataframe.loc[base & ob_touch, "enter_tag"] = "order_block_pullback_v1"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        trend_break = dataframe["close"] < dataframe["ema50"]
        local_exhaustion = dataframe["rsi"] > 76
        volatility_break = (dataframe["atr"] / dataframe["close"]) > 0.035
        dataframe.loc[trend_break | local_exhaustion | volatility_break, "exit_long"] = 1
        return dataframe
