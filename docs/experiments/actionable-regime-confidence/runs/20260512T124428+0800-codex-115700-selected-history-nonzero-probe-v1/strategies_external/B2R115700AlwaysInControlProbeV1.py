"""
B2R115700AlwaysInControlProbeV1

Harness control for the 115700 selected-history workspace. This intentionally
forces frequent entries with a zero-threshold ROI so we can distinguish
"strategy too selective" from "Freqtrade/data harness cannot close trades".

This is chain-contract / harness evidence only. It must not be promoted as a
market factor or profitable recipe.

# AUTO_QUANT_META v1
Strategy:        B2R115700AlwaysInControlProbeV1
Mutation_id:     115700-selected-history-always-in-control-probe-v1
Base_factor:     harness_control_always_in
Hypothesis:      Frequent entries with immediate ROI eligibility should create
                 closed-trade observations if the selected-history Freqtrade
                 harness is capable of trading this synthetic pair.
Paradigm:        harness-control
Expected_regime: control
Branch_path:     Bull -> ProviderCryptoMomentum -> HarnessControl -> AlwaysInControlProbeV1
Factors_used:    none_control_probe
Parent:          115700_selected_history
Asset_class:     synthetic_ohlcv
Status:          diagnostic_control
# END_AUTO_QUANT_META
"""
from __future__ import annotations

from freqtrade.strategy import IStrategy
from pandas import DataFrame


class B2R115700AlwaysInControlProbeV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 0.0}
    stoploss = -0.99

    process_only_new_candles = True
    use_exit_signal = False
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 1

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["close"].notna(), "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe
