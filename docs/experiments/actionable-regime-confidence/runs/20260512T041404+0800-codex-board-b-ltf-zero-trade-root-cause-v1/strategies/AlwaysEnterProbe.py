from __future__ import annotations

from pandas import DataFrame

from freqtrade.strategy import IStrategy


class AlwaysEnterProbe(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 0.01}
    stoploss = -0.10
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 1

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        probe_slot = dataframe.index.to_series() % 10
        dataframe.loc[(dataframe["volume"] > 0) & (probe_slot == 0), ["enter_long", "enter_tag"]] = (
            1,
            "always_enter_probe",
        )
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        probe_slot = dataframe.index.to_series() % 10
        dataframe.loc[(dataframe["volume"] > 0) & (probe_slot == 5), "exit_long"] = 1
        return dataframe
