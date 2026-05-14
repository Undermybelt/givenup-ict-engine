from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class ObFvgRetestContinuationLongV1(IStrategy):
    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 0.018, "24": 0}
    stoploss = -0.035
    startup_candle_count = 120

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["atr14"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["rsi14"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["swing_high"] = dataframe["high"].rolling(20, min_periods=5).max()
        dataframe["swing_low"] = dataframe["low"].rolling(20, min_periods=5).min()
        dataframe["bull_fvg"] = dataframe["low"] > dataframe["high"].shift(2)
        dataframe["bear_fvg"] = dataframe["high"] < dataframe["low"].shift(2)
        dataframe["bull_fvg_mid"] = (dataframe["low"] + dataframe["high"].shift(2)) / 2.0
        dataframe["bear_fvg_mid"] = (dataframe["high"] + dataframe["low"].shift(2)) / 2.0
        dataframe["bull_order_block"] = (
            (dataframe["close"].shift(1) < dataframe["open"].shift(1))
            & (dataframe["close"] > dataframe["high"].shift(1))
            & (dataframe["close"] > dataframe["ema20"])
        )
        dataframe["bear_order_block"] = (
            (dataframe["close"].shift(1) > dataframe["open"].shift(1))
            & (dataframe["close"] < dataframe["low"].shift(1))
            & (dataframe["close"] < dataframe["ema20"])
        )
        dataframe["volume_z"] = (
            dataframe["volume"] - dataframe["volume"].rolling(48, min_periods=12).mean()
        ) / dataframe["volume"].rolling(48, min_periods=12).std()
        swing_range = (dataframe["swing_high"] - dataframe["swing_low"]).replace(0, 1)
        dataframe["ote_position"] = (dataframe["close"] - dataframe["swing_low"]) / swing_range
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        long_trend = (dataframe["ema20"] > dataframe["ema50"]) & (dataframe["close"] > dataframe["ema20"])
        short_trend = (dataframe["ema20"] < dataframe["ema50"]) & (dataframe["close"] < dataframe["ema20"])
        bull_fvg_retest = dataframe["bull_fvg"].rolling(12, min_periods=1).max().fillna(0).astype(bool) & (
            dataframe["low"] <= dataframe["bull_fvg_mid"].rolling(12, min_periods=1).max()
        )
        bear_fvg_retest = dataframe["bear_fvg"].rolling(12, min_periods=1).max().fillna(0).astype(bool) & (
            dataframe["high"] >= dataframe["bear_fvg_mid"].rolling(12, min_periods=1).min()
        )
        bull_ob_retest = dataframe["bull_order_block"].rolling(16, min_periods=1).max().fillna(0).astype(bool) & (
            dataframe["low"] <= dataframe["open"].shift(1).rolling(16, min_periods=1).max()
        )
        bear_ob_retest = dataframe["bear_order_block"].rolling(16, min_periods=1).max().fillna(0).astype(bool) & (
            dataframe["high"] >= dataframe["open"].shift(1).rolling(16, min_periods=1).min()
        )
        displacement = dataframe["volume_z"] > 0.8
        ote_zone = dataframe["ote_position"].between(0.50, 0.786)
        smt_proxy = dataframe["volume_z"].between(-0.25, 1.25) & (dataframe["rsi14"] > 48)
        failed_mitigation = (dataframe["rsi14"].between(45, 55)) & (dataframe["atr14"] > 0)
        condition = long_trend & bull_fvg_retest & (dataframe["close"] > dataframe["open"])
        dataframe.loc[condition, ["enter_long", "enter_tag"]] = (1, "fvg_retest_continuation_long_v1")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["rsi14"] > 72)
                | (dataframe["close"] < dataframe["ema20"] * 0.985)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "ob_fvg_long_exit_v1")
        dataframe.loc[
            (
                (dataframe["rsi14"] < 28)
                | (dataframe["close"] > dataframe["ema20"] * 1.015)
            ),
            ["exit_short", "exit_tag"],
        ] = (1, "ob_fvg_short_exit_v1")
        return dataframe
