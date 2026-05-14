from __future__ import annotations

from freqtrade.strategy import IStrategy
from pandas import DataFrame


class ProviderRegimeProbeV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.045
    trailing_stop = True
    trailing_stop_positive = 0.008
    trailing_stop_positive_offset = 0.018
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count = 120

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = dataframe["close"].ewm(span=20, adjust=False).mean()
        dataframe["ema80"] = dataframe["close"].ewm(span=80, adjust=False).mean()
        prev_close = dataframe["close"].shift(1)
        tr1 = dataframe["high"] - dataframe["low"]
        tr2 = (dataframe["high"] - prev_close).abs()
        tr3 = (dataframe["low"] - prev_close).abs()
        dataframe["atr14"] = tr1.combine(tr2, max).combine(tr3, max).rolling(14, min_periods=7).mean()
        delta = dataframe["close"].diff()
        gain = delta.clip(lower=0).rolling(14, min_periods=7).mean()
        loss = (-delta.clip(upper=0)).rolling(14, min_periods=7).mean()
        rs = gain / loss.replace(0, 1e-9)
        dataframe["rsi14"] = 100 - (100 / (1 + rs))
        dataframe["trend_strength"] = (dataframe["ema20"] - dataframe["ema80"]) / dataframe["close"]
        dataframe["vol_floor"] = dataframe["volume"].rolling(24, min_periods=6).median().fillna(0) * 0.25
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        mask = (
            (dataframe["close"] > dataframe["ema20"])
            & (dataframe["ema20"] > dataframe["ema80"])
            & (dataframe["trend_strength"] > 0.0015)
            & (dataframe["rsi14"].between(42, 72))
            & (dataframe["volume"] >= dataframe["vol_floor"])
        )
        dataframe.loc[mask, "enter_long"] = 1
        dataframe.loc[mask, "enter_tag"] = "provider_regime_probe_long"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        mask = (
            (dataframe["close"] < dataframe["ema20"])
            | (dataframe["trend_strength"] < -0.001)
            | (dataframe["rsi14"] > 80)
        )
        dataframe.loc[mask, "exit_long"] = 1
        return dataframe
