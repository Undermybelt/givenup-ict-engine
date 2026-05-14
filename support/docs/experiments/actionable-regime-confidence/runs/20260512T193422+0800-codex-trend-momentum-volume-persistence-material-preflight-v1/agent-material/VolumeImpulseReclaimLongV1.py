from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class VolumeImpulseReclaimLongV1(IStrategy):
    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 0.016, "24": 0}
    stoploss = -0.032
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
        condition = (dataframe["ema12"] > dataframe["ema48"]) & (dataframe["close"] > dataframe["ema12"]) & (dataframe["rsi14"] > 51) & (dataframe["volume_z"] > 0.15) & (dataframe["close"] > dataframe["open"])
        dataframe.loc[condition, ["enter_long", "enter_tag"]] = (1, "volume_impulse_reclaim_long_v1")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["rsi14"] > 74) | (dataframe["close"] < dataframe["ema12"] * 0.985), ["exit_long", "exit_tag"]] = (1, "volume_impulse_reclaim_long_v1_exit")
        return dataframe
