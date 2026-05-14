from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class ProviderSessionLiquidityVwapOpeningRangeV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.028
    trailing_stop = True
    trailing_stop_positive = 0.010
    trailing_stop_positive_offset = 0.022
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count: int = 240

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["hour_utc"] = dataframe["date"].dt.hour

        typical = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3.0
        volume = dataframe["volume"].clip(lower=1)
        dataframe["vwap_24"] = (typical * volume).rolling(24, min_periods=8).sum() / volume.rolling(24, min_periods=8).sum()
        dataframe["session_high_8"] = dataframe["high"].rolling(8, min_periods=4).max().shift(1)
        dataframe["session_low_8"] = dataframe["low"].rolling(8, min_periods=4).min().shift(1)
        dataframe["opening_range_high"] = dataframe["high"].rolling(3, min_periods=2).max().shift(1)
        dataframe["opening_range_low"] = dataframe["low"].rolling(3, min_periods=2).min().shift(1)
        dataframe["range_24"] = (dataframe["high"].rolling(24, min_periods=12).max() - dataframe["low"].rolling(24, min_periods=12).min())
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["compression"] = dataframe["range_24"] < dataframe["atr"].rolling(24, min_periods=12).mean() * 9.0
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""

        liquid = dataframe["hour_utc"].between(0, 23)
        bull = liquid & (dataframe["ema20"] > dataframe["ema50"]) & (dataframe["close"] > dataframe["ema200"])
        sideways = liquid & (dataframe["close"] > dataframe["session_low_8"]) & (dataframe["close"] < dataframe["session_high_8"])
        relief = liquid & (dataframe["close"] < dataframe["ema200"]) & (dataframe["rsi"] < 48)
        transition = liquid & dataframe["compression"] & (dataframe["atr_pct"] > 0.0015)

        orb = bull & (dataframe["close"] > dataframe["opening_range_high"]) & (dataframe["close"] > dataframe["vwap_24"])
        vwap_reclaim = sideways & (dataframe["low"] < dataframe["vwap_24"]) & (dataframe["close"] > dataframe["vwap_24"])
        sweep_reclaim = relief & (dataframe["low"] < dataframe["session_low_8"]) & (dataframe["close"] > dataframe["session_low_8"])
        compression_release = transition & (dataframe["close"] > dataframe["session_high_8"]) & (dataframe["close"] > dataframe["ema20"])

        dataframe.loc[orb, "enter_long"] = 1
        dataframe.loc[orb, "enter_tag"] = "session_orb_vwap_continuation_long_v1"
        dataframe.loc[vwap_reclaim, "enter_long"] = 1
        dataframe.loc[vwap_reclaim, "enter_tag"] = "session_vwap_reclaim_long_v1"
        dataframe.loc[sweep_reclaim, "enter_long"] = 1
        dataframe.loc[sweep_reclaim, "enter_tag"] = "session_sweep_reclaim_long_v1"
        dataframe.loc[compression_release, "enter_long"] = 1
        dataframe.loc[compression_release, "enter_tag"] = "session_late_compression_release_v1"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        vwap_loss = dataframe["close"] < dataframe["vwap_24"]
        trend_loss = dataframe["close"] < dataframe["ema50"]
        exhaustion = dataframe["rsi"] > 76
        dataframe.loc[vwap_loss | trend_loss | exhaustion, "exit_long"] = 1
        return dataframe
