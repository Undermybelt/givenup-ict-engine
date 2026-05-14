from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class ProviderHighDensityRsiBbEmaV1(IStrategy):
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
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 220

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        bb = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe["bb_lower"] = bb["lowerband"]
        dataframe["bb_mid"] = bb["middleband"]
        dataframe["bb_upper"] = bb["upperband"]
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["hour_utc"] = dataframe["date"].dt.hour
        dataframe["volume_sma20"] = dataframe["volume"].rolling(20, min_periods=10).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""

        liquid = (dataframe["hour_utc"] >= 0) & (dataframe["hour_utc"] <= 23)
        valid_vol = dataframe["atr_pct"].between(0.0015, 0.060)
        vol_ok = dataframe["volume"] >= (dataframe["volume_sma20"] * 0.35)

        range_revert = (
            liquid
            & valid_vol
            & vol_ok
            & (dataframe["close"] <= dataframe["bb_lower"] * 1.004)
            & dataframe["rsi"].between(24, 46)
            & (dataframe["close"] > dataframe["open"])
        )
        trend_pullback = (
            liquid
            & valid_vol
            & vol_ok
            & (dataframe["ema20"] > dataframe["ema50"])
            & (dataframe["close"] > dataframe["ema200"])
            & (dataframe["low"] <= dataframe["ema20"] + dataframe["atr"] * 0.35)
            & dataframe["rsi"].between(38, 58)
            & (dataframe["close"] > dataframe["open"])
        )
        bb_breakout = (
            liquid
            & valid_vol
            & vol_ok
            & (dataframe["close"] > dataframe["bb_upper"])
            & (dataframe["ema20"] > dataframe["ema50"])
            & dataframe["rsi"].between(52, 72)
        )
        risk_suppression = (
            liquid
            & valid_vol
            & vol_ok
            & (dataframe["close"] > dataframe["ema50"])
            & dataframe["rsi"].between(44, 60)
            & (dataframe["atr_pct"] <= 0.035)
        )

        leaves = [
            (range_revert, "hd_rsi_bb_revert_v1"),
            (trend_pullback, "hd_ema_atr_pullback_v1"),
            (bb_breakout, "hd_bb_breakout_v1"),
            (risk_suppression, "hd_risk_suppression_v1"),
        ]
        for condition, tag in leaves:
            dataframe.loc[condition, "enter_long"] = 1
            dataframe.loc[condition, "enter_tag"] = tag
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        exit_signal = (
            (dataframe["close"] < dataframe["ema50"])
            | (dataframe["rsi"] > 76)
            | (dataframe["atr_pct"] > 0.070)
        )
        dataframe.loc[exit_signal, "exit_long"] = 1
        return dataframe
