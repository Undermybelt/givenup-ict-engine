from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class ProviderSessionVwapLiquidityV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.028

    trailing_stop = True
    trailing_stop_positive = 0.010
    trailing_stop_positive_offset = 0.024
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count: int = 120

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["hour_utc"] = dataframe["date"].dt.hour
        dataframe["session_date"] = dataframe["date"].dt.date

        typical = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3.0
        pv = typical * dataframe["volume"].clip(lower=0)
        cum_pv = pv.groupby(dataframe["session_date"]).cumsum()
        cum_volume = dataframe["volume"].clip(lower=0).groupby(dataframe["session_date"]).cumsum()
        dataframe["session_vwap"] = cum_pv / cum_volume.replace(0, float("nan"))

        dataframe["opening_range_high"] = dataframe["high"].groupby(dataframe["session_date"]).transform(
            lambda values: values.head(3).max()
        )
        dataframe["opening_range_low"] = dataframe["low"].groupby(dataframe["session_date"]).transform(
            lambda values: values.head(3).min()
        )
        dataframe["volume_ma24"] = dataframe["volume"].rolling(24, min_periods=12).mean()
        dataframe["volume_impulse"] = dataframe["volume"] > dataframe["volume_ma24"] * 1.18
        dataframe["atr_ratio"] = dataframe["atr"] / dataframe["close"]
        dataframe["vwap_distance_atr"] = (dataframe["close"] - dataframe["session_vwap"]) / dataframe["atr"]
        dataframe["liquid_window"] = dataframe["hour_utc"].between(0, 23)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""

        liquid = dataframe["liquid_window"] & dataframe["session_vwap"].notna() & dataframe["atr"].notna()
        normal_vol = dataframe["atr_ratio"].between(0.0015, 0.055)
        low_liquidity = dataframe["volume"] < dataframe["volume_ma24"] * 0.55

        fade = (
            liquid
            & normal_vol
            & (dataframe["vwap_distance_atr"] < -0.70)
            & (dataframe["rsi"].between(28, 48))
            & (dataframe["close"] > dataframe["low"].shift(1))
            & ~low_liquidity
        )
        retest = (
            liquid
            & normal_vol
            & (dataframe["ema20"] > dataframe["ema50"])
            & (dataframe["low"] <= dataframe["opening_range_high"])
            & (dataframe["close"] > dataframe["opening_range_high"])
            & (dataframe["rsi"].between(42, 68))
            & ~low_liquidity
        )
        impulse = (
            liquid
            & dataframe["volume_impulse"]
            & (dataframe["close"] > dataframe["opening_range_high"])
            & (dataframe["close"] > dataframe["session_vwap"])
            & (dataframe["atr_ratio"].between(0.002, 0.070))
            & (dataframe["rsi"].between(46, 74))
            & ~low_liquidity
        )

        dataframe.loc[fade, "enter_long"] = 1
        dataframe.loc[fade, "enter_tag"] = "session_vwap_fade_liquidity_v1"
        dataframe.loc[retest, "enter_long"] = 1
        dataframe.loc[retest, "enter_tag"] = "session_opening_range_retest_v1"
        dataframe.loc[impulse, "enter_long"] = 1
        dataframe.loc[impulse, "enter_tag"] = "session_liquidity_impulse_breakout_v1"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        low_liquidity = dataframe["volume"] < dataframe["volume_ma24"] * 0.45
        vwap_reclaim_exhausted = (dataframe["close"] > dataframe["session_vwap"]) & (dataframe["rsi"] > 70)
        trend_loss = dataframe["close"] < dataframe["ema50"]
        dataframe.loc[low_liquidity | vwap_reclaim_exhausted | trend_loss, "exit_long"] = 1
        return dataframe
