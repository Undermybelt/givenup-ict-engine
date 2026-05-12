from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class ProviderDenseSnapbackV1(IStrategy):
    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 0.018, "12": 0.009, "36": 0}
    stoploss = -0.035
    startup_candle_count = 80

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["rsi2"] = ta.RSI(dataframe, timeperiod=2)
        dataframe["rsi14"] = ta.RSI(dataframe, timeperiod=14)
        bb = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe["bb_lower"] = bb["lowerband"]
        dataframe["bb_mid"] = bb["middleband"]
        dataframe["bb_upper"] = bb["upperband"]
        dataframe["atr14"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["keltn_lower"] = dataframe["ema20"] - (1.5 * dataframe["atr14"])
        dataframe["vol_sma20"] = dataframe["volume"].rolling(20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["rsi2"] < 12)
                & (dataframe["close"] <= dataframe["bb_lower"] * 1.004)
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "rsi2_lower_tail_snapback_v1")
        dataframe.loc[
            (
                (dataframe["close"].shift(1) < dataframe["bb_lower"].shift(1))
                & (dataframe["close"] > dataframe["bb_lower"])
                & (dataframe["rsi14"] > dataframe["rsi14"].shift(1))
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "bb_lower_band_snapback_v1")
        dataframe.loc[
            (
                (dataframe["low"] <= dataframe["keltn_lower"])
                & (dataframe["close"] > dataframe["keltn_lower"])
                & (dataframe["close"] > dataframe["open"])
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "keltner_lower_band_snapback_v1")
        dataframe.loc[
            (
                (dataframe["close"].shift(1) < dataframe["ema20"].shift(1))
                & (dataframe["close"] > dataframe["ema20"])
                & (dataframe["ema20"] >= dataframe["ema50"] * 0.995)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "ema20_reclaim_continuation_v1")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["close"] >= dataframe["bb_mid"])
                | (dataframe["rsi14"] > 68)
                | (dataframe["close"] < dataframe["ema50"] * 0.985)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "snapback_exit_v1")
        return dataframe
