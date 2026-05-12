from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class ProviderVwapSessionLiquidityV1(IStrategy):
    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 0.014, "10": 0.007, "30": 0}
    stoploss = -0.032
    startup_candle_count = 96

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["atr14"] = ta.ATR(dataframe, timeperiod=14)
        typical = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3.0
        cum_volume = dataframe["volume"].rolling(24, min_periods=4).sum()
        dataframe["vwap24"] = (typical * dataframe["volume"]).rolling(24, min_periods=4).sum() / cum_volume
        dataframe["vwap_dist_atr"] = (dataframe["close"] - dataframe["vwap24"]) / dataframe["atr14"]
        dataframe["session_high24"] = dataframe["high"].rolling(24).max()
        dataframe["session_low24"] = dataframe["low"].rolling(24).min()
        dataframe["session_range_atr"] = (dataframe["session_high24"] - dataframe["session_low24"]) / dataframe["atr14"]
        vol_mean = dataframe["volume"].rolling(48, min_periods=12).mean()
        vol_std = dataframe["volume"].rolling(48, min_periods=12).std()
        dataframe["volume_z"] = (dataframe["volume"] - vol_mean) / vol_std
        dataframe["low_liquidity"] = dataframe["volume"] < (vol_mean * 0.55)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["close"].shift(1) < dataframe["vwap24"].shift(1))
                & (dataframe["close"] > dataframe["vwap24"])
                & (dataframe["vwap_dist_atr"].between(-0.15, 0.75))
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "vwap_reclaim_long_v1")
        dataframe.loc[
            (
                (dataframe["close"] > dataframe["session_high24"].shift(1))
                & (dataframe["session_range_atr"] > 1.2)
                & (dataframe["volume_z"] > 0.35)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "session_range_breakout_long_v1")
        dataframe.loc[
            (
                (dataframe["volume_z"] > 1.15)
                & (dataframe["close"] > dataframe["ema20"])
                & (dataframe["session_range_atr"].between(0.55, 2.6))
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "volume_zscore_expansion_long_v1")
        dataframe.loc[
            (
                (dataframe["low_liquidity"])
                | (dataframe["vwap_dist_atr"] > 2.4)
                | (dataframe["atr14"] <= 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (0, "liquidity_guard_v1")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["close"] < dataframe["vwap24"] * 0.992)
                | (dataframe["vwap_dist_atr"] > 1.8)
                | (dataframe["volume_z"] < -0.8)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "vwap_session_exit_v1")
        return dataframe
