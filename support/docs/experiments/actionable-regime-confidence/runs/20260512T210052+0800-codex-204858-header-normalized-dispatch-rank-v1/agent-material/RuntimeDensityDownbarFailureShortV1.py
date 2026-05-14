from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class RuntimeDensityDownbarFailureShortV1(IStrategy):
    timeframe = "1h"
    can_short = True
    minimal_roi = {"0": 0.004, "12": 0}
    stoploss = -0.014
    startup_candle_count = 30

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi14"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        condition = (dataframe["close"] < dataframe["open"]) & (dataframe["volume"] > 0)
        dataframe.loc[condition, ["enter_short", "enter_tag"]] = (1, "runtime_density_downbar_failure_short_v1")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["close"] > dataframe["open"]) | (dataframe["rsi14"] < 26), ["exit_short", "exit_tag"]] = (1, "runtime_density_downbar_failure_short_v1_exit")
        return dataframe
