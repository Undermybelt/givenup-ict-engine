from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class RuntimeDensityUpbarReclaimLongV1(IStrategy):
    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 0.004, "12": 0}
    stoploss = -0.014
    startup_candle_count = 30

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi14"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        condition = (dataframe["close"] > dataframe["open"]) & (dataframe["volume"] > 0)
        dataframe.loc[condition, ["enter_long", "enter_tag"]] = (1, "runtime_density_upbar_reclaim_long_v1")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["close"] < dataframe["open"]) | (dataframe["rsi14"] > 74), ["exit_long", "exit_tag"]] = (1, "runtime_density_upbar_reclaim_long_v1_exit")
        return dataframe
