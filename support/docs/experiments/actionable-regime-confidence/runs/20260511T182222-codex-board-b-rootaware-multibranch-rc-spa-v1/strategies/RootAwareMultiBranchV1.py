"""
RootAwareMultiBranchV1 - Board B additive regime-root strategy.

Bull branch trades VolBreakoutSized's Donchian/4h-trend/volume setup.
Bear, Sideways, and Crisis are explicit suppress/no-trade roots for this
candidate because the source-root readback showed negative branch edge there.
"""

from __future__ import annotations

import bisect
from pathlib import Path

import pandas as pd
from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


SOURCE_REGIME_CSV = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)


def _load_source_roots() -> tuple[list[pd.Timestamp], dict[pd.Timestamp, str]]:
    rows = pd.read_csv(SOURCE_REGIME_CSV, usecols=["date", "regime_label"])
    rows["date"] = pd.to_datetime(rows["date"]).dt.tz_localize(None)
    grouped = rows.groupby(["date", "regime_label"], observed=True).size().unstack(fill_value=0)
    daily = {pd.Timestamp(date): str(counts.idxmax()) for date, counts in grouped.iterrows()}
    return sorted(daily), daily


SOURCE_DATES, SOURCE_ROOTS = _load_source_roots()


def _lookup_root(value) -> str:
    ts = pd.Timestamp(value)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    date = ts.normalize()
    if date in SOURCE_ROOTS:
        return SOURCE_ROOTS[date]
    pos = bisect.bisect_right(SOURCE_DATES, date) - 1
    if pos >= 0:
        prev = SOURCE_DATES[pos]
        if 0 <= int((date - prev).days) <= 3:
            return SOURCE_ROOTS[prev]
    return "unknown"


class RootAwareMultiBranchV1(IStrategy):
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

    startup_candle_count: int = 250

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["source_root"] = dataframe["date"].map(_lookup_root)
        dataframe["source_root_is_bull"] = (dataframe["source_root"] == "Bull").astype(int)
        dataframe["donchian_high_24"] = dataframe["high"].rolling(24).max().shift(1)
        dataframe["sma50"] = ta.SMA(dataframe, timeperiod=50)
        dataframe["volume_sma20"] = dataframe["volume"].rolling(20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        bull_branch = (
            (dataframe["source_root_is_bull"] == 1)
            & (dataframe["close"] > dataframe["donchian_high_24"])
            & (dataframe["ema50_4h"] > dataframe["ema200_4h"])
            & (dataframe["volume"] > 1.3 * dataframe["volume_sma20"])
        )
        dataframe.loc[bull_branch, ["enter_long", "enter_tag"]] = (
            1,
            "Bull->TrendExpansion->Donchian24Ema4hTrendVolumeVolTarget->RootAwareMultiBranchV1",
        )
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["close"] < dataframe["sma50"], "exit_long"] = 1
        return dataframe

    def custom_stake_amount(
        self,
        pair: str,
        current_time,
        current_rate: float,
        proposed_stake: float,
        min_stake,
        max_stake: float,
        leverage: float,
        entry_tag: str,
        side: str,
        **kwargs,
    ) -> float:
        df, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if df.empty or "atr_pct_4h" not in df.columns:
            return proposed_stake
        atr_pct = df["atr_pct_4h"].iloc[-1]
        if atr_pct != atr_pct or atr_pct <= 0:
            return proposed_stake
        scale = min(1.0, 0.003 / float(atr_pct))
        stake = proposed_stake * scale
        return max(min_stake or 0.0, min(max_stake, stake))
