"""RootAwareRegimeSwitch - additive Board B root-aware Auto-Quant recipe.

This strategy is intentionally kept in the experiment run directory. It uses
Board A daily market-regime context as a root gate and emits branch-specific
entry tags. It is not installed into the Auto-Quant checkout or ict-engine.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


SOURCE_PANEL = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)

ROOT_TO_CODE = {
    "Bull": 1,
    "Bear": 2,
    "Sideways": 3,
    "Crisis": 4,
}

_DAILY_ROOT_CONTEXT: DataFrame | None = None


def daily_root_context() -> DataFrame:
    global _DAILY_ROOT_CONTEXT
    if _DAILY_ROOT_CONTEXT is not None:
        return _DAILY_ROOT_CONTEXT
    df = pd.read_csv(
        SOURCE_PANEL,
        usecols=["date", "ticker", "regime_label", "regime_confidence"],
    )
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.normalize()
    counts = (
        df.groupby(["date", "regime_label"], as_index=False)
        .agg(
            ticker_count=("ticker", "nunique"),
            row_count=("ticker", "size"),
            mean_source_confidence=("regime_confidence", "mean"),
        )
        .sort_values(
            ["date", "row_count", "mean_source_confidence", "regime_label"],
            ascending=[True, False, False, True],
        )
    )
    daily = counts.groupby("date", as_index=False).first()
    daily["root_code"] = daily["regime_label"].map(ROOT_TO_CODE).fillna(0).astype(int)
    _DAILY_ROOT_CONTEXT = daily[["date", "regime_label", "root_code"]].sort_values("date")
    return _DAILY_ROOT_CONTEXT


class RootAwareRegimeSwitch(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.99
    trailing_stop = False
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 760
    pair_basket = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "AVAX/USDT"]
    test_timeranges = [("full_5y", "20210101-20251231")]

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        return dataframe

    def _attach_root_context(self, dataframe: DataFrame) -> DataFrame:
        ctx = daily_root_context()
        left = pd.DataFrame(
            {
                "__idx": range(len(dataframe)),
                "date_norm": pd.to_datetime(dataframe["date"], utc=True).dt.normalize(),
            }
        ).sort_values("date_norm")
        merged = pd.merge_asof(
            left,
            ctx,
            left_on="date_norm",
            right_on="date",
            direction="backward",
        ).sort_values("__idx")
        dataframe["market_regime_root"] = merged["regime_label"].fillna("Unlabeled").values
        dataframe["market_regime_root_code"] = merged["root_code"].fillna(0).astype(int).values
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = self._attach_root_context(dataframe)
        dataframe["donchian_high_24"] = dataframe["high"].rolling(24).max().shift(1)
        dataframe["high_30d"] = dataframe["high"].rolling(720).max().shift(1)
        dataframe["drawdown_pct"] = dataframe["close"] / dataframe["high_30d"] - 1.0
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["sma50"] = ta.SMA(dataframe, timeperiod=50)
        bb = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe["bb_lower"] = bb["lowerband"]
        dataframe["volume_sma20"] = dataframe["volume"].rolling(20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        bull_breakout = (
            (dataframe["market_regime_root_code"] == ROOT_TO_CODE["Bull"])
            & (dataframe["close"] > dataframe["donchian_high_24"])
            & (dataframe["ema50_4h"] > dataframe["ema200_4h"])
            & (dataframe["volume"] > 1.1 * dataframe["volume_sma20"])
        )
        bear_rebound = (
            (dataframe["market_regime_root_code"] == ROOT_TO_CODE["Bear"])
            & (dataframe["drawdown_pct"] < -0.20)
            & (dataframe["rsi"] < 35)
            & (dataframe["volume"] > dataframe["volume_sma20"])
        )
        sideways_reversion = (
            (dataframe["market_regime_root_code"] == ROOT_TO_CODE["Sideways"])
            & (dataframe["close"] < dataframe["bb_lower"])
            & (dataframe["rsi"] < 32)
            & (dataframe["volume"] > 0)
        )

        dataframe.loc[bull_breakout, ["enter_long", "enter_tag"]] = (
            1,
            "Bull->TrendExpansion->VolBreakout->RootAwareRegimeSwitch",
        )
        dataframe.loc[bear_rebound, ["enter_long", "enter_tag"]] = (
            1,
            "Bear->BearMarketDrawdown->CapitulationBounce->RootAwareRegimeSwitch",
        )
        dataframe.loc[sideways_reversion, ["enter_long", "enter_tag"]] = (
            1,
            "Sideways->RangeStress->MeanReversion->RootAwareRegimeSwitch",
        )
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        crisis_suppress = dataframe["market_regime_root_code"] == ROOT_TO_CODE["Crisis"]
        trend_exit = dataframe["close"] < dataframe["sma50"]
        rebound_exit = dataframe["rsi"] > 52
        dataframe.loc[crisis_suppress | trend_exit | rebound_exit, "exit_long"] = 1
        return dataframe
