#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


SCRIPT = Path(__file__).resolve()
BASE_SCRIPT = SCRIPT.with_name("run_ibkr_mgc1m_vortex_trend_continuation_7d_gate1_v1.py")
spec = importlib.util.spec_from_file_location("ibkr_gate1_template", BASE_SCRIPT)
base = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = base
spec.loader.exec_module(base)

STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
base.ROOT = base.BASE / "runs" / f"{STAMP}-codex-ibkr-mgc1m-hma-pullback-7d-gate1-v1"
base.SOURCE_ROOT = base.BASE / "runs/20260519T232924+0800-codex-ibkr-mgc1m-opening-vwap-rvol-reclaim-7d-gate1-v1"
base.SOURCE_DATA = base.SOURCE_ROOT / "data/provider/normalized/ibkr_mgc_202606_1m_7d.csv"
base.AQ_SYMBOL = "IBKR_MGC1M_HMA_PULLBACK_7D_GATE1_V1"
base.FACTOR_ID = "ibkr_mgc1m_hma_pullback_7d_gate1_v1"
base.BRANCH_PATH = "TrendPullback -> HullMaPullback -> ibkr_mgc1m_hma_pullback_7d_gate1_v1"
base.ROOT_SYMBOL = "MGC"
base.PRODUCT = "precious_metals"
base.EXCHANGE = "COMEX"
base.MULTIPLIER = "10"
base.CONTRACT_FILE_TOKEN = "mgc"
base.LAST_TRADE_DATE = "202606"
base.SOURCE_BACKED_FAMILY = "Hull Moving Average / HMA pullback continuation"
base.SUMMARY_TABLE_TITLE = "Exact MGC 1m HMA pullback rows:"
base.DOWNSTREAM_DECISION = "gate1_ibkr_mgc1m_hma_pullback_downstream_allowed"
base.BLOCKED_DECISION = "drop_or_block_gate1_practical"


@dataclass(frozen=True)
class Variant:
    name: str
    hma_fast: int
    hma_slow: int
    slope_lookback: int
    fast_slope_min: float
    slow_slope_min: float
    rvol_min: float
    pullback_atr_max: float
    rsi_min: float
    rsi_max: float
    roi: float
    stoploss: float
    trail: float
    offset: float


base.VARIANTS = [
    Variant("hma_dense", 16, 49, 6, -0.020, -0.020, 0.42, 1.20, 38.0, 78.0, 0.0022, -0.0060, 0.0008, 0.0022),
    Variant("hma_balanced", 21, 55, 8, 0.000, -0.006, 0.52, 0.95, 42.0, 76.0, 0.0030, -0.0070, 0.0010, 0.0030),
    Variant("hma_quality", 34, 89, 10, 0.012, 0.004, 0.68, 0.72, 45.0, 74.0, 0.0040, -0.0082, 0.0013, 0.0040),
    Variant("hma_reclaim", 16, 55, 6, 0.008, -0.012, 0.48, 1.35, 40.0, 80.0, 0.0026, -0.0065, 0.0009, 0.0026),
]


def class_name(variant: Variant) -> str:
    safe = "".join(part.title() for part in variant.name.split("_"))
    return f"IbkrMgcHullMaPullback{safe}1MinV1"


def label_for(row: dict) -> str:
    package = str(row.get("package_id") or "")
    variant = next((item.name for item in base.VARIANTS if item.name.replace("_", "-") in package), "unknown")
    return f"MGC/{variant}/1m"


def strategy_source(name: str, variant: Variant) -> str:
    tag = f"{base.FACTOR_ID}_{variant.name}"
    return f'''from freqtrade.strategy import IStrategy
from pandas import DataFrame


class {name}(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1m"
    can_short = False
    minimal_roi = {{"0": {variant.roi}}}
    stoploss = {variant.stoploss}
    trailing_stop = True
    trailing_stop_positive = {variant.trail}
    trailing_stop_positive_offset = {variant.offset}
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count = 320

    def _wma(self, series, period: int):
        weights = list(range(1, period + 1))
        scale = float(sum(weights))
        return series.rolling(period).apply(lambda values: sum(values[i] * weights[i] for i in range(period)) / scale, raw=True)

    def _hma(self, series, period: int):
        half = max(2, period // 2)
        root = max(2, int(period ** 0.5))
        return self._wma(2.0 * self._wma(series, half) - self._wma(series, period), root)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        high = dataframe["high"]
        low = dataframe["low"]
        close = dataframe["close"]
        prev_close = close.shift()
        tr = DataFrame({{"hl": high - low, "hc": (high - prev_close).abs(), "lc": (low - prev_close).abs()}}).max(axis=1)
        dataframe["atr"] = tr.rolling(14).mean()
        dataframe["hma_fast"] = self._hma(close, {variant.hma_fast})
        dataframe["hma_slow"] = self._hma(close, {variant.hma_slow})
        dataframe["ema144"] = close.ewm(span=144, adjust=False).mean()
        dataframe["fast_slope_atr"] = (dataframe["hma_fast"] - dataframe["hma_fast"].shift({variant.slope_lookback})) / dataframe["atr"].replace(0, 1)
        dataframe["slow_slope_atr"] = (dataframe["hma_slow"] - dataframe["hma_slow"].shift({variant.slope_lookback})) / dataframe["atr"].replace(0, 1)
        dataframe["pullback_atr"] = (close - dataframe["hma_fast"]).abs() / dataframe["atr"].replace(0, 1)
        dataframe["rvol"] = dataframe["volume"] / dataframe["volume"].rolling(60).mean().replace(0, 1)
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean().replace(0, 1e-9)
        dataframe["rsi14"] = 100.0 - (100.0 / (1.0 + gain / loss))
        minute = dataframe["date"].dt.hour * 60 + dataframe["date"].dt.minute
        dataframe["entry_window"] = ((minute >= 13 * 60 + 35) & (minute <= 20 * 60 + 35)) | ((minute >= 0) & (minute <= 2 * 60 + 10))
        dataframe["force_exit_window"] = (minute >= 20 * 60 + 50) & (minute < 21 * 60 + 55)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        signal = (
            dataframe["entry_window"]
            & (dataframe["hma_fast"] >= dataframe["hma_slow"])
            & (dataframe["fast_slope_atr"].fillna(0) >= {variant.fast_slope_min})
            & (dataframe["slow_slope_atr"].fillna(0) >= {variant.slow_slope_min})
            & (dataframe["close"] >= dataframe["ema144"] - dataframe["atr"] * 0.35)
            & (dataframe["pullback_atr"] <= {variant.pullback_atr_max})
            & (dataframe["rvol"] >= {variant.rvol_min})
            & dataframe["rsi14"].between({variant.rsi_min}, {variant.rsi_max})
        )
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{tag}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        slope_lost = dataframe["fast_slope_atr"] < -0.030
        cross_lost = dataframe["hma_fast"] < dataframe["hma_slow"]
        trend_lost = dataframe["close"] < dataframe["hma_fast"] - dataframe["atr"] * 0.60
        dataframe.loc[dataframe["force_exit_window"] | slope_lost | cross_lost | trend_lost, "exit_long"] = 1
        return dataframe
'''


def write_materials(data_path: Path) -> list[Path]:
    materials: list[Path] = []
    for variant in base.VARIANTS:
        klass = class_name(variant)
        strategy = base.ROOT / "agent-material" / f"{klass}.py"
        strategy.write_text(strategy_source(klass, variant), encoding="utf-8")
        material = base.ROOT / "agent-material" / f"ibkr_mgc_hma_pullback_{variant.name}_1m_7d_v1.material.json"
        payload = {
            "package_id": f"ibkr-mgc-hma-pullback-{variant.name.replace('_', '-')}-1m-7d-v1",
            "title": f"IBKR MGC Hull MA pullback {variant.name} 1m 7D",
            "symbol": "MGC",
            "timeframe": "1m",
            "timerange": base.timerange(data_path),
            "direction": "long",
            "data_path": str(data_path),
            "strategy_source_path": str(strategy),
            "strategy_class_name": klass,
            "strategy_brief": "Classic Hull Moving Average pullback-continuation on retained real IBKR MGC 1m futures data; public-family diversity lane distinct from VWAP/RSI/RVOL, liquidity sweep, Donchian, Keltner, Vortex, RVI, Chaikin, Qstick, EOM, and Schaff roots.",
            "evaluation_priority": ["public_family_diversity", "hma_pullback", "exact_1m_cost_density"],
            "consumer_evidence_profile": {
                "branch_path": base.BRANCH_PATH,
                "regime_profit_branch_path": base.BRANCH_PATH,
                "branch_id": base.FACTOR_ID,
                "market": "FUTURES",
                "product": "precious_metals",
                "root_symbol": "MGC",
                "root_timeframe": "1m",
                "main_regime": "TrendPullback",
                "sub_regime": "HullMaPullback",
                "sub_sub_regime_or_profit_factor": base.FACTOR_ID,
                "profit_factor": base.FACTOR_ID,
                "base_timeframe": "1m",
                "training_timeframe": "1m",
                "material_timeframe": "1m",
                "provider": "IBKR",
                "provider_window": "7 D",
                "provider_provenance": f"IBKR FUT MGC 202606 1m 7 D retained source={base.SOURCE_ROOT.name}",
                "source_backed_family": "Hull Moving Average / HMA pullback continuation",
                "asset_class": "futures",
                "sec_type": "FUT",
                "exchange": "COMEX",
                "multiplier": "10",
                "last_trade_date": "202606",
                "gate_id": "Gate1IbkrMgcHmaPullback1m7d",
                "promotion_allowed": False,
                "trade_usable": False,
                "update_goal": False,
            },
            "notes": ["public_family=hull_moving_average", "local_cache_replay=false_retained_real_ibkr_same_session", "downstream_forbidden_until_cost_density_survives"],
        }
        material.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        materials.append(material)
    return materials


base.class_name = class_name
base.label_for = label_for
base.strategy_source = strategy_source
base.write_materials = write_materials


if __name__ == "__main__":
    raise SystemExit(base.main())
