from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class ProviderHighDensityMultiBranchV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.045

    trailing_stop = True
    trailing_stop_positive = 0.008
    trailing_stop_positive_offset = 0.018
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count: int = 240

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema12"] = ta.EMA(dataframe, timeperiod=12)
        dataframe["ema24"] = ta.EMA(dataframe, timeperiod=24)
        dataframe["ema72"] = ta.EMA(dataframe, timeperiod=72)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["volume_sma"] = ta.SMA(dataframe["volume"], timeperiod=30)
        dataframe["donchian_high"] = dataframe["high"].rolling(48).max().shift(1)
        dataframe["bb_mid"] = ta.SMA(dataframe["close"], timeperiod=20)
        dataframe["bb_std"] = dataframe["close"].rolling(20).std()
        dataframe["bb_low"] = dataframe["bb_mid"] - dataframe["bb_std"] * 2.0
        dataframe["atr_sma"] = ta.SMA(dataframe["atr"], timeperiod=50)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""

        trend = (dataframe["ema12"] > dataframe["ema24"]) & (dataframe["ema24"] > dataframe["ema72"])
        normal_vol = dataframe["atr_pct"].between(0.004, 0.035)
        high_vol = dataframe["atr_pct"].between(0.018, 0.070)
        compression = (dataframe["atr"] < dataframe["atr_sma"] * 0.82) & normal_vol
        reclaim = (dataframe["close"] > dataframe["ema12"]) & (dataframe["close"].shift(1) <= dataframe["ema12"].shift(1))
        pullback = trend & normal_vol & reclaim & dataframe["rsi"].between(42, 63)
        breakout = trend & high_vol & (dataframe["close"] > dataframe["donchian_high"]) & (dataframe["volume"] > dataframe["volume_sma"] * 1.10)
        reversion = normal_vol & (dataframe["close"].shift(1) < dataframe["bb_low"].shift(1)) & (dataframe["close"] > dataframe["bb_low"]) & dataframe["rsi"].between(28, 48)
        compression_breakout = compression.shift(1).fillna(False) & (dataframe["close"] > dataframe["high"].shift(1)) & (dataframe["volume"] > dataframe["volume_sma"])

        dataframe.loc[pullback, "enter_long"] = 1
        dataframe.loc[pullback, "enter_tag"] = "ema_rsi_pullback_density_v1"
        dataframe.loc[breakout, "enter_long"] = 1
        dataframe.loc[breakout, "enter_tag"] = "donchian_volume_breakout_density_v1"
        dataframe.loc[reversion, "enter_long"] = 1
        dataframe.loc[reversion, "enter_tag"] = "rsi_bollinger_reversion_density_v1"
        dataframe.loc[compression_breakout, "enter_long"] = 1
        dataframe.loc[compression_breakout, "enter_tag"] = "atr_compression_breakout_density_v1"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        exit_trend_break = dataframe["close"] < dataframe["ema24"]
        exit_overheat = dataframe["rsi"] > 76
        exit_vol_spike = dataframe["atr_pct"] > 0.085
        dataframe.loc[exit_trend_break | exit_overheat | exit_vol_spike, "exit_long"] = 1
        return dataframe
