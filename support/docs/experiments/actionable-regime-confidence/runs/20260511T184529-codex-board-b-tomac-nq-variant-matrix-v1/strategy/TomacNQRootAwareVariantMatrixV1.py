from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy, informative
from pandas import DataFrame


class _TomacNQVariantBase(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 100}
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 250

    breakout_window = 24
    breakdown_window = 24
    killzone_start = 13
    killzone_end = 15
    ema_fast_period = 21
    ema_slow_period = 89
    trend_mode = "strict"

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=self.ema_fast_period)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=self.ema_slow_period)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["high_n"] = dataframe["high"].rolling(self.breakout_window).max().shift(1)
        dataframe["low_n"] = dataframe["low"].rolling(self.breakdown_window).min().shift(1)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["hour_utc"] = dataframe["date"].dt.hour
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        in_window = (
            (dataframe["hour_utc"] >= self.killzone_start)
            & (dataframe["hour_utc"] <= self.killzone_end)
        )
        breakout = dataframe["close"] > dataframe["high_n"]
        if self.trend_mode == "loose":
            trend = dataframe["ema_fast_4h"] >= (dataframe["ema_slow_4h"] * 0.985)
        else:
            trend = dataframe["ema_fast_4h"] > dataframe["ema_slow_4h"]
        dataframe.loc[in_window & breakout & trend, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        breakdown = dataframe["close"] < dataframe["low_n"]
        trend_break = dataframe["ema_fast_4h"] < dataframe["ema_slow_4h"]
        dataframe.loc[breakdown | trend_break, "exit_long"] = 1
        return dataframe

class TomacNQVariantBaseline(_TomacNQVariantBase):
    stoploss = -0.02
    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.01
    trailing_only_offset_is_reached = True
    breakout_window = 24
    breakdown_window = 24
    killzone_start = 13
    killzone_end = 15
    ema_fast_period = 21
    ema_slow_period = 89
    trend_mode = 'strict'


class TomacNQVariantTightTrail(_TomacNQVariantBase):
    stoploss = -0.015
    trailing_stop = True
    trailing_stop_positive = 0.003
    trailing_stop_positive_offset = 0.006
    trailing_only_offset_is_reached = True
    breakout_window = 24
    breakdown_window = 18
    killzone_start = 13
    killzone_end = 16
    ema_fast_period = 21
    ema_slow_period = 89
    trend_mode = 'strict'


class TomacNQVariantDenseSession(_TomacNQVariantBase):
    stoploss = -0.02
    trailing_stop = True
    trailing_stop_positive = 0.004
    trailing_stop_positive_offset = 0.008
    trailing_only_offset_is_reached = True
    breakout_window = 12
    breakdown_window = 12
    killzone_start = 12
    killzone_end = 17
    ema_fast_period = 13
    ema_slow_period = 55
    trend_mode = 'strict'


class TomacNQVariantConservativeTrend(_TomacNQVariantBase):
    stoploss = -0.012
    trailing_stop = True
    trailing_stop_positive = 0.004
    trailing_stop_positive_offset = 0.008
    trailing_only_offset_is_reached = True
    breakout_window = 48
    breakdown_window = 24
    killzone_start = 13
    killzone_end = 15
    ema_fast_period = 34
    ema_slow_period = 144
    trend_mode = 'strict'


class TomacNQVariantLooseCrisis(_TomacNQVariantBase):
    stoploss = -0.03
    trailing_stop = True
    trailing_stop_positive = 0.006
    trailing_stop_positive_offset = 0.012
    trailing_only_offset_is_reached = True
    breakout_window = 8
    breakdown_window = 8
    killzone_start = 13
    killzone_end = 20
    ema_fast_period = 8
    ema_slow_period = 34
    trend_mode = 'loose'


class TomacNQVariantBearSidewaysDense(_TomacNQVariantBase):
    stoploss = -0.018
    trailing_stop = True
    trailing_stop_positive = 0.003
    trailing_stop_positive_offset = 0.006
    trailing_only_offset_is_reached = True
    breakout_window = 6
    breakdown_window = 6
    killzone_start = 10
    killzone_end = 20
    ema_fast_period = 8
    ema_slow_period = 34
    trend_mode = 'loose'


class TomacNQVariantFullDayTrend(_TomacNQVariantBase):
    stoploss = -0.02
    trailing_stop = True
    trailing_stop_positive = 0.004
    trailing_stop_positive_offset = 0.008
    trailing_only_offset_is_reached = True
    breakout_window = 24
    breakdown_window = 18
    killzone_start = 0
    killzone_end = 23
    ema_fast_period = 21
    ema_slow_period = 89
    trend_mode = 'strict'
