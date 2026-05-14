from __future__ import annotations

from freqtrade.strategy import IStrategy
from pandas import DataFrame


class ProviderTrendPullbackResume(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.035

    trailing_stop = True
    trailing_stop_positive = 0.006
    trailing_stop_positive_offset = 0.014
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 80

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        high = dataframe["high"]
        low = dataframe["low"]

        dataframe["ema_fast"] = close.ewm(span=12, adjust=False).mean()
        dataframe["ema_slow"] = close.ewm(span=48, adjust=False).mean()
        dataframe["momentum_24"] = close.pct_change(24)
        dataframe["momentum_12"] = close.pct_change(12)
        dataframe["range_24"] = (high.rolling(24).max() - low.rolling(24).min()) / close
        dataframe["pullback_depth"] = (close - dataframe["ema_fast"]) / close
        dataframe["volume_floor"] = dataframe["volume"].rolling(24).median().fillna(0.0)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        trend_intact = dataframe["ema_fast"] > dataframe["ema_slow"]
        pullback_near_fast_ema = dataframe["pullback_depth"].between(-0.012, 0.004)
        recent_momentum_positive = dataframe["momentum_24"] > 0.0025
        range_not_extreme = dataframe["range_24"].between(0.004, 0.09)
        liquid = dataframe["volume"] >= dataframe["volume_floor"].fillna(0.0)

        dataframe.loc[
            trend_intact
            & pullback_near_fast_ema
            & recent_momentum_positive
            & range_not_extreme
            & liquid,
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        trend_break = dataframe["close"] < dataframe["ema_slow"]
        momentum_flip = dataframe["momentum_12"] < -0.004
        dataframe.loc[trend_break | momentum_flip, "exit_long"] = 1
        return dataframe
