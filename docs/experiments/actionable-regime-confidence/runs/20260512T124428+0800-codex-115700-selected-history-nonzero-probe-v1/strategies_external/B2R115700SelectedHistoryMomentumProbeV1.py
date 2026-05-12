"""
B2R115700SelectedHistoryMomentumProbeV1

Purpose: selected-history nonzero-trade probe for the 115700 Board B lane.
This strategy is intentionally isolated under a docs/experiments run root and
is not part of ict-engine runtime code or the managed Auto-Quant checkout.

# AUTO_QUANT_META v1
Strategy:        B2R115700SelectedHistoryMomentumProbeV1
Mutation_id:     115700-selected-history-nonzero-probe-v1
Base_factor:     selected_history_momentum_probe
Hypothesis:      In the selected 1h same-root provider/AQ history, a simple EMA
                 momentum continuation probe should create nonzero observations
                 for measurement. It is a diagnostic recipe, not promotion
                 evidence by itself.
Paradigm:        momentum-continuation
Expected_regime: Bull.ProviderCryptoMomentum.RsiMidlineExpansion
Branch_path:     Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> SelectedHistoryMomentumProbeV1
Factors_used:    ema8_ema21_rsi_midline_continuation
Parent:          115700_selected_history
Asset_class:     synthetic_ohlcv
Status:          diagnostic
# END_AUTO_QUANT_META
"""
from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class B2R115700SelectedHistoryMomentumProbeV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 0.012, "12": 0.004}
    stoploss = -0.025

    trailing_stop = True
    trailing_stop_positive = 0.004
    trailing_stop_positive_offset = 0.009
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 30

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema8"] = ta.EMA(dataframe, timeperiod=8)
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["prev_close"] = dataframe["close"].shift(1)
        dataframe["close_3"] = dataframe["close"].shift(3)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        momentum = dataframe["ema8"] > dataframe["ema21"]
        rsi_midline = (dataframe["rsi"] >= 48) & (dataframe["rsi"] <= 72)
        continuation = dataframe["close"] > dataframe["close_3"]
        range_ok = (dataframe["atr"] / dataframe["close"]) > 0.002
        dataframe.loc[
            momentum & rsi_midline & continuation & range_ok,
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        momentum_break = dataframe["ema8"] < dataframe["ema21"]
        rsi_exhaustion = dataframe["rsi"] > 78
        close_break = dataframe["close"] < dataframe["ema8"]
        dataframe.loc[momentum_break | rsi_exhaustion | close_break, "exit_long"] = 1
        return dataframe
