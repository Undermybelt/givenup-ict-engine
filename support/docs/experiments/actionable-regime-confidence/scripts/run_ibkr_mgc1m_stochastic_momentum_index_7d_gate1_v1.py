#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


SCRIPT = Path(__file__).resolve()
BASE_SCRIPT = SCRIPT.with_name("run_ibkr_mgc1m_vortex_trend_continuation_7d_gate1_v1.py")
spec = importlib.util.spec_from_file_location("mgc_vortex_gate1_template", BASE_SCRIPT)
base = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = base
spec.loader.exec_module(base)

STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
base.ROOT = base.BASE / "runs" / f"{STAMP}-codex-ibkr-mgc1m-stochastic-momentum-index-7d-gate1-v1"
base.AQ_SYMBOL = "IBKR_MGC1M_STOCHASTIC_MOMENTUM_INDEX_7D_GATE1_V1"
base.FACTOR_ID = "ibkr_mgc1m_stochastic_momentum_index_7d_gate1_v1"
base.BRANCH_PATH = "MomentumReclaim -> StochasticMomentumIndex -> ibkr_mgc1m_stochastic_momentum_index_7d_gate1_v1"
base.SOURCE_BACKED_FAMILY = "Stochastic Momentum Index oscillator reclaim"
base.SUMMARY_TABLE_TITLE = "Exact MGC 1m Stochastic Momentum Index rows:"
base.DOWNSTREAM_DECISION = "gate1_ibkr_mgc1m_stochastic_momentum_index_downstream_allowed"

base.VARIANTS = [
    base.Variant("smi_dense", 8, -22.0, 2.0, 0.45, -0.040, 1.05, 0.0024, -0.0062, 0.0008, 0.0024),
    base.Variant("smi_balanced", 10, -15.0, 2.8, 0.55, -0.020, 0.88, 0.0030, -0.0070, 0.0010, 0.0030),
    base.Variant("smi_quality", 13, -8.0, 3.5, 0.68, 0.000, 0.72, 0.0040, -0.0082, 0.0013, 0.0040),
    base.Variant("smi_zero_reclaim", 8, -3.0, 1.8, 0.50, -0.030, 0.95, 0.0028, -0.0068, 0.0009, 0.0028),
]


def class_name(variant: base.Variant) -> str:
    safe = "".join(part.title() for part in variant.name.split("_"))
    return f"IbkrMgcStochasticMomentumIndex{safe}1MinV1"


def label_for(row: dict) -> str:
    package = str(row.get("package_id") or "")
    variant = next((item.name for item in base.VARIANTS if item.name.replace("_", "-") in package), "unknown")
    return f"MGC/{variant}/1m"


def strategy_source(name: str, variant: base.Variant) -> str:
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
    startup_candle_count = 260

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        high = dataframe["high"]
        low = dataframe["low"]
        close = dataframe["close"]
        prev_close = close.shift()
        tr = DataFrame({{"hl": high - low, "hc": (high - prev_close).abs(), "lc": (low - prev_close).abs()}}).max(axis=1)
        dataframe["atr"] = tr.rolling(14).mean()
        dataframe["ema21"] = close.ewm(span=21, adjust=False).mean()
        dataframe["ema55"] = close.ewm(span=55, adjust=False).mean()
        dataframe["ema144"] = close.ewm(span=144, adjust=False).mean()
        dataframe["ema_slope_atr"] = (dataframe["ema21"] - dataframe["ema21"].shift(10)) / dataframe["atr"].replace(0, 1)
        dataframe["rvol"] = dataframe["volume"] / dataframe["volume"].rolling(60).mean().replace(0, 1)
        hh = high.rolling({variant.vi_period}).max()
        ll = low.rolling({variant.vi_period}).min()
        midpoint = (hh + ll) / 2.0
        distance = close - midpoint
        range_half = ((hh - ll) / 2.0).replace(0, 1e-9)
        rel = 100.0 * distance / range_half
        dataframe["smi"] = rel.ewm(span=3, adjust=False).mean().ewm(span=3, adjust=False).mean()
        dataframe["smi_signal"] = dataframe["smi"].ewm(span=3, adjust=False).mean()
        dataframe["smi_slope"] = dataframe["smi"] - dataframe["smi"].shift(3)
        dataframe["pullback_atr"] = (close - dataframe["ema21"]).abs() / dataframe["atr"].replace(0, 1)
        minute = dataframe["date"].dt.hour * 60 + dataframe["date"].dt.minute
        dataframe["entry_window"] = ((minute >= 13 * 60 + 35) & (minute <= 20 * 60 + 35)) | ((minute >= 0) & (minute <= 2 * 60 + 10))
        dataframe["force_exit_window"] = (minute >= 20 * 60 + 50) & (minute < 21 * 60 + 55)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        reclaim = (dataframe["smi"] > dataframe["smi_signal"]) & (dataframe["smi"].shift(1) <= dataframe["smi_signal"].shift(1))
        signal = (
            dataframe["entry_window"]
            & reclaim
            & (dataframe["smi"].shift(1) <= {variant.vi_spread_min})
            & (dataframe["smi_slope"].fillna(0) >= {variant.vi_slope_min})
            & (dataframe["ema_slope_atr"].fillna(0) >= {variant.ema_slope_min})
            & (dataframe["close"] >= dataframe["ema144"] - dataframe["atr"] * 0.35)
            & (dataframe["pullback_atr"] <= {variant.pullback_atr_max})
            & (dataframe["rvol"] >= {variant.rvol_min})
        )
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{tag}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        smi_rollover = dataframe["smi"] < dataframe["smi_signal"]
        momentum_lost = dataframe["close"] < dataframe["ema21"] - dataframe["atr"] * 0.50
        dataframe.loc[dataframe["force_exit_window"] | smi_rollover | momentum_lost, "exit_long"] = 1
        return dataframe
'''


def write_materials(data_path: Path) -> list[Path]:
    materials: list[Path] = []
    for variant in base.VARIANTS:
        klass = class_name(variant)
        strategy = base.ROOT / "agent-material" / f"{klass}.py"
        strategy.write_text(strategy_source(klass, variant), encoding="utf-8")
        material = base.ROOT / "agent-material" / f"ibkr_mgc_stochastic_momentum_index_{variant.name}_1m_7d_v1.material.json"
        payload = {
            "package_id": f"ibkr-mgc-stochastic-momentum-index-{variant.name.replace('_', '-')}-1m-7d-v1",
            "title": f"IBKR MGC Stochastic Momentum Index {variant.name} 1m 7D",
            "symbol": "MGC",
            "timeframe": "1m",
            "timerange": base.timerange(data_path),
            "direction": "long",
            "data_path": str(data_path),
            "strategy_source_path": str(strategy),
            "strategy_class_name": klass,
            "strategy_brief": "Classic Stochastic Momentum Index oscillator-reclaim family on retained real IBKR MGC 1m futures data; diversity lane distinct from VWAP/RSI/RVOL, adaptive moving averages, Choppiness, and MGC/SI relative-value probes.",
            "evaluation_priority": ["public_family_diversity", "exact_1m_cost_density", "precious_metals_provider_parity"],
            "consumer_evidence_profile": {
                "branch_path": base.BRANCH_PATH,
                "regime_profit_branch_path": base.BRANCH_PATH,
                "branch_id": base.FACTOR_ID,
                "market": "FUTURES",
                "product": "precious_metals",
                "root_symbol": "MGC",
                "root_timeframe": "1m",
                "main_regime": "MomentumReclaim",
                "sub_regime": "StochasticMomentumIndex",
                "sub_sub_regime_or_profit_factor": base.FACTOR_ID,
                "profit_factor": base.FACTOR_ID,
                "base_timeframe": "1m",
                "training_timeframe": "1m",
                "material_timeframe": "1m",
                "provider": "IBKR",
                "provider_window": "7 D",
                "provider_provenance": f"IBKR FUT MGC 202606 1m 7 D source={base.SOURCE_ROOT.name}",
                "source_backed_family": "Stochastic Momentum Index oscillator reclaim",
                "asset_class": "futures",
                "sec_type": "FUT",
                "exchange": "COMEX",
                "multiplier": "10",
                "last_trade_date": "202606",
                "gate_id": "Gate1IbkrMgcStochasticMomentumIndex1m7d",
                "promotion_allowed": False,
                "trade_usable": False,
                "update_goal": False,
            },
            "notes": ["public_family=stochastic_momentum_index", "local_cache_replay=false_source_provider_root_reused", "downstream_forbidden_until_cost_density_survives"],
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
