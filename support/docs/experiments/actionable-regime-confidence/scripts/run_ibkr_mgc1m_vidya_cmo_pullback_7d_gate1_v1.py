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
base.ROOT = base.BASE / "runs" / f"{STAMP}-codex-ibkr-mgc1m-vidya-cmo-pullback-7d-gate1-v1"
base.SOURCE_ROOT = base.BASE / "runs/20260519T232924+0800-codex-ibkr-mgc1m-opening-vwap-rvol-reclaim-7d-gate1-v1"
base.SOURCE_DATA = base.SOURCE_ROOT / "data/provider/normalized/ibkr_mgc_202606_1m_7d.csv"
base.AQ_SYMBOL = "IBKR_MGC1M_VIDYA_CMO_PULLBACK_7D_GATE1_V1"
base.FACTOR_ID = "ibkr_mgc1m_vidya_cmo_pullback_7d_gate1_v1"
base.BRANCH_PATH = "TrendEfficiency -> VidyaCmoAdaptivePullback -> ibkr_mgc1m_vidya_cmo_pullback_7d_gate1_v1"
base.ROOT_SYMBOL = "MGC"
base.PRODUCT = "precious_metals"
base.EXCHANGE = "COMEX"
base.MULTIPLIER = "10"
base.CONTRACT_FILE_TOKEN = "mgc"
base.LAST_TRADE_DATE = "202606"
base.SOURCE_BACKED_FAMILY = "VIDYA / CMO adaptive moving-average pullback"
base.SUMMARY_TABLE_TITLE = "Exact MGC 1m VIDYA/CMO adaptive pullback rows:"
base.DOWNSTREAM_DECISION = "gate1_ibkr_mgc1m_vidya_cmo_pullback_downstream_allowed"
base.BLOCKED_DECISION = "drop_or_block_gate1_practical"


@dataclass(frozen=True)
class Variant:
    name: str
    cmo_period: int
    vidya_fast: int
    vidya_slow: int
    slope_lookback: int
    slope_min: float
    cmo_min: float
    rvol_min: float
    pullback_atr_max: float
    roi: float
    stoploss: float
    trail: float
    offset: float


base.VARIANTS = [
    Variant("vidya_dense", 9, 10, 45, 6, -0.020, 2.0, 0.40, 1.15, 0.0022, -0.0060, 0.0008, 0.0022),
    Variant("vidya_balanced", 14, 14, 55, 8, 0.000, 5.0, 0.52, 0.90, 0.0030, -0.0070, 0.0010, 0.0030),
    Variant("vidya_quality", 18, 18, 72, 10, 0.012, 9.0, 0.68, 0.68, 0.0040, -0.0082, 0.0013, 0.0040),
    Variant("vidya_reclaim", 9, 10, 55, 6, 0.006, -2.0, 0.46, 1.30, 0.0026, -0.0065, 0.0009, 0.0026),
]


def class_name(variant: Variant) -> str:
    safe = "".join(part.title() for part in variant.name.split("_"))
    return f"IbkrMgcVidyaCmoPullback{safe}1MinV1"


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

    def _vidya(self, close, cmo_abs, period: int):
        alpha = 2.0 / (period + 1.0)
        return (close * alpha * cmo_abs + close.shift().ewm(span=period, adjust=False).mean() * (1.0 - alpha * cmo_abs)).ewm(span=3, adjust=False).mean()

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        high = dataframe["high"]
        low = dataframe["low"]
        close = dataframe["close"]
        prev_close = close.shift()
        tr = DataFrame({{"hl": high - low, "hc": (high - prev_close).abs(), "lc": (low - prev_close).abs()}}).max(axis=1)
        dataframe["atr"] = tr.rolling(14).mean()
        delta = close.diff()
        up = delta.clip(lower=0).rolling({variant.cmo_period}).sum()
        down = (-delta.clip(upper=0)).rolling({variant.cmo_period}).sum()
        dataframe["cmo"] = 100.0 * (up - down) / (up + down).replace(0, 1e-9)
        dataframe["cmo_abs"] = dataframe["cmo"].abs().clip(0, 100) / 100.0
        dataframe["vidya_fast"] = self._vidya(close, dataframe["cmo_abs"], {variant.vidya_fast})
        dataframe["vidya_slow"] = self._vidya(close, dataframe["cmo_abs"], {variant.vidya_slow})
        dataframe["ema144"] = close.ewm(span=144, adjust=False).mean()
        dataframe["vidya_slope_atr"] = (dataframe["vidya_fast"] - dataframe["vidya_fast"].shift({variant.slope_lookback})) / dataframe["atr"].replace(0, 1)
        dataframe["pullback_atr"] = (close - dataframe["vidya_fast"]).abs() / dataframe["atr"].replace(0, 1)
        dataframe["rvol"] = dataframe["volume"] / dataframe["volume"].rolling(60).mean().replace(0, 1)
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
            & (dataframe["vidya_fast"] >= dataframe["vidya_slow"])
            & (dataframe["vidya_slope_atr"].fillna(0) >= {variant.slope_min})
            & (dataframe["cmo"].fillna(0) >= {variant.cmo_min})
            & (dataframe["close"] >= dataframe["ema144"] - dataframe["atr"] * 0.35)
            & (dataframe["pullback_atr"] <= {variant.pullback_atr_max})
            & (dataframe["rvol"] >= {variant.rvol_min})
            & dataframe["rsi14"].between(40, 80)
        )
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{tag}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        cmo_lost = dataframe["cmo"] < -5.0
        trend_lost = dataframe["close"] < dataframe["vidya_fast"] - dataframe["atr"] * 0.55
        cross_lost = dataframe["vidya_fast"] < dataframe["vidya_slow"]
        dataframe.loc[dataframe["force_exit_window"] | cmo_lost | trend_lost | cross_lost, "exit_long"] = 1
        return dataframe
'''


def write_materials(data_path: Path) -> list[Path]:
    materials: list[Path] = []
    for variant in base.VARIANTS:
        klass = class_name(variant)
        strategy = base.ROOT / "agent-material" / f"{klass}.py"
        strategy.write_text(strategy_source(klass, variant), encoding="utf-8")
        material = base.ROOT / "agent-material" / f"ibkr_mgc_vidya_cmo_pullback_{variant.name}_1m_7d_v1.material.json"
        payload = {
            "package_id": f"ibkr-mgc-vidya-cmo-pullback-{variant.name.replace('_', '-')}-1m-7d-v1",
            "title": f"IBKR MGC VIDYA CMO adaptive pullback {variant.name} 1m 7D",
            "symbol": "MGC",
            "timeframe": "1m",
            "timerange": base.timerange(data_path),
            "direction": "long",
            "data_path": str(data_path),
            "strategy_source_path": str(strategy),
            "strategy_class_name": klass,
            "strategy_brief": "Public VIDYA / CMO adaptive moving-average pullback on retained real IBKR MGC 1m futures data; distinct from MAMA/FAMA, HMA, Vortex, RVI, pivots, PSAR, Keltner, Donchian, and VWAP/RSI/RVOL roots.",
            "evaluation_priority": ["public_family_diversity", "vidya_cmo_adaptive_pullback", "exact_1m_cost_density"],
            "consumer_evidence_profile": {
                "branch_path": base.BRANCH_PATH,
                "regime_profit_branch_path": base.BRANCH_PATH,
                "branch_id": base.FACTOR_ID,
                "market": "FUTURES",
                "product": "precious_metals",
                "root_symbol": "MGC",
                "root_timeframe": "1m",
                "main_regime": "TrendEfficiency",
                "sub_regime": "VidyaCmoAdaptivePullback",
                "sub_sub_regime_or_profit_factor": base.FACTOR_ID,
                "profit_factor": base.FACTOR_ID,
                "base_timeframe": "1m",
                "training_timeframe": "1m",
                "material_timeframe": "1m",
                "provider": "IBKR",
                "provider_window": "7 D",
                "provider_provenance": f"IBKR FUT MGC 202606 1m 7 D retained source={base.SOURCE_ROOT.name}",
                "source_backed_family": "VIDYA / CMO adaptive moving-average pullback",
                "asset_class": "futures",
                "sec_type": "FUT",
                "exchange": "COMEX",
                "multiplier": "10",
                "last_trade_date": "202606",
                "gate_id": "Gate1IbkrMgcVidyaCmoPullback1m7d",
                "promotion_allowed": False,
                "trade_usable": False,
                "update_goal": False,
            },
            "notes": ["public_family=vidya_cmo_adaptive_ma", "local_cache_replay=false_retained_real_ibkr_same_session", "downstream_forbidden_until_cost_density_survives"],
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
