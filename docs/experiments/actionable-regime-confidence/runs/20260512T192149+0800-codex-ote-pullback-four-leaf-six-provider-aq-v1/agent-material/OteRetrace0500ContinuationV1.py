from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class OteRetrace0500ContinuationV1(IStrategy):
    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 0.018, "12": 0.009, "36": 0}
    stoploss = -0.034
    startup_candle_count = 120
    ote_level = 0.500

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["atr14"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["swing_high48"] = dataframe["high"].rolling(48, min_periods=24).max()
        dataframe["swing_low48"] = dataframe["low"].rolling(48, min_periods=24).min()
        dataframe["leg_range48"] = dataframe["swing_high48"] - dataframe["swing_low48"]
        dataframe["ote_price"] = dataframe["swing_high48"] - (dataframe["leg_range48"] * self.ote_level)
        dataframe["ote_dist_atr"] = (dataframe["close"] - dataframe["ote_price"]).abs() / dataframe["atr14"]
        dataframe["trend_stack"] = (dataframe["ema20"] > dataframe["ema50"]) & (dataframe["ema50"] > dataframe["ema200"])
        dataframe["pullback_depth"] = (dataframe["swing_high48"] - dataframe["close"]) / dataframe["leg_range48"]
        dataframe["volume_mean48"] = dataframe["volume"].rolling(48, min_periods=12).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["trend_stack"]
                & (dataframe["leg_range48"] > dataframe["atr14"] * 2.0)
                & (dataframe["pullback_depth"].between(self.ote_level - 0.045, self.ote_level + 0.045))
                & (dataframe["ote_dist_atr"] <= 0.55)
                & (dataframe["close"] > dataframe["open"])
                & (dataframe["close"] > dataframe["low"].shift(1))
                & (dataframe["volume"] > dataframe["volume_mean48"] * 0.55)
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "ote_retrace_0500_continuation_v1")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["close"] >= dataframe["swing_high48"].shift(1) * 0.997)
                | (dataframe["close"] < dataframe["ema50"])
                | (dataframe["pullback_depth"] > min(self.ote_level + 0.16, 0.94))
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "ote_retrace_0500_exit_v1")
        return dataframe
