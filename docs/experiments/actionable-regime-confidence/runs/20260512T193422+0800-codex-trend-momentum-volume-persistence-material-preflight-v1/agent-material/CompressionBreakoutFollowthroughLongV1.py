from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class CompressionBreakoutFollowthroughLongV1(IStrategy):
    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 0.018, "24": 0}
    stoploss = -0.035
    startup_candle_count = 120

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema12"] = ta.EMA(dataframe, timeperiod=12)
        dataframe["ema24"] = ta.EMA(dataframe, timeperiod=24)
        dataframe["ema48"] = ta.EMA(dataframe, timeperiod=48)
        dataframe["atr14"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["rsi14"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr14"] / dataframe["close"].replace(0, 1)
        volume_std = dataframe["volume"].rolling(48, min_periods=12).std().replace(0, 1)
        dataframe["volume_z"] = (
            dataframe["volume"] - dataframe["volume"].rolling(48, min_periods=12).mean()
        ) / volume_std
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        condition = (dataframe["atr_pct"] < dataframe["atr_pct"].rolling(96, min_periods=24).median()) & (dataframe["close"] > dataframe["high"].shift(1).rolling(24, min_periods=8).max()) & (dataframe["volume_z"] > -0.25)
        dataframe.loc[condition, ["enter_long", "enter_tag"]] = (1, "compression_breakout_followthrough_long_v1")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["close"] < dataframe["ema24"]) | (dataframe["rsi14"] > 76), ["exit_long", "exit_tag"]] = (1, "compression_breakout_followthrough_long_v1_exit")
        return dataframe
