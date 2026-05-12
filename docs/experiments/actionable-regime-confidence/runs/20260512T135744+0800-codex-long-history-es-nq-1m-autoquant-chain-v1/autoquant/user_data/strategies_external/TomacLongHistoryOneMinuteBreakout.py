from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy, informative
from pandas import DataFrame


class TomacLongHistoryOneMinuteBreakout(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1m"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.006

    trailing_stop = True
    trailing_stop_positive = 0.0025
    trailing_stop_positive_offset = 0.005
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 1500

    @informative("15m")
    def populate_indicators_15m(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=89)
        return dataframe

    @informative("1h")
    def populate_indicators_1h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=8)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=21)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["high_120m"] = dataframe["high"].rolling(120).max().shift(1)
        dataframe["low_120m"] = dataframe["low"].rolling(120).min().shift(1)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=30)
        dataframe["hour_utc"] = dataframe["date"].dt.hour
        dataframe["minute_utc"] = dataframe["date"].dt.minute
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        am_killzone = (dataframe["hour_utc"] >= 13) & (dataframe["hour_utc"] <= 15)
        breakout = dataframe["close"] > dataframe["high_120m"]
        trend_15m = dataframe["ema_fast_15m"] > dataframe["ema_slow_15m"]
        trend_1h = dataframe["ema_fast_1h"] > dataframe["ema_slow_1h"]
        dataframe.loc[
            am_killzone & breakout & trend_15m & trend_1h,
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        breakdown = dataframe["close"] < dataframe["low_120m"]
        trend_break_15m = dataframe["ema_fast_15m"] < dataframe["ema_slow_15m"]
        dataframe.loc[breakdown | trend_break_15m, "exit_long"] = 1
        return dataframe
