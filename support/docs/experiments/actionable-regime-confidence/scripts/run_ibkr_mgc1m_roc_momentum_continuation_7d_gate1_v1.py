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
base.ROOT = base.BASE / "runs" / f"{STAMP}-codex-ibkr-mgc1m-roc-momentum-continuation-7d-gate1-v1"
base.SOURCE_ROOT = base.BASE / "runs/20260519T232924+0800-codex-ibkr-mgc1m-opening-vwap-rvol-reclaim-7d-gate1-v1"
base.SOURCE_DATA = base.SOURCE_ROOT / "data/provider/normalized/ibkr_mgc_202606_1m_7d.csv"
base.AQ_SYMBOL = "IBKR_MGC1M_ROC_MOMENTUM_CONTINUATION_7D_GATE1_V1"
base.FACTOR_ID = "ibkr_mgc1m_roc_momentum_continuation_7d_gate1_v1"
base.BRANCH_PATH = "MomentumContinuation -> RateOfChangeMomentum -> ibkr_mgc1m_roc_momentum_continuation_7d_gate1_v1"
base.ROOT_SYMBOL = "MGC"
base.PRODUCT = "precious_metals"
base.EXCHANGE = "COMEX"
base.MULTIPLIER = "10"
base.CONTRACT_FILE_TOKEN = "mgc"
base.LAST_TRADE_DATE = "202606"
base.SOURCE_BACKED_FAMILY = "Rate of Change / ROC momentum continuation"
base.SUMMARY_TABLE_TITLE = "Exact MGC 1m ROC momentum-continuation rows:"
base.DOWNSTREAM_DECISION = "gate1_ibkr_mgc1m_roc_momentum_continuation_downstream_allowed"
base.BLOCKED_DECISION = "drop_or_block_gate1_practical"


@dataclass(frozen=True)
class Variant:
    name: str
    roc_period: int
    roc_min: float
    roc_slope_min: float
    rvol_min: float
    ema_slope_min: float
    pullback_atr_max: float
    rsi_min: float
    rsi_max: float
    roi: float
    stoploss: float
    trail: float
    offset: float


base.VARIANTS = [
    Variant("roc_dense", 8, 0.00018, -0.00004, 0.36, -0.026, 1.20, 38.0, 82.0, 0.0020, -0.0058, 0.0007, 0.0020),
    Variant("roc_reclaim", 12, 0.00006, 0.00000, 0.44, -0.016, 1.00, 40.0, 80.0, 0.0025, -0.0064, 0.0009, 0.0025),
    Variant("roc_balanced", 16, 0.00028, 0.00004, 0.54, -0.004, 0.80, 42.0, 78.0, 0.0030, -0.0072, 0.0010, 0.0030),
    Variant("roc_quality", 24, 0.00048, 0.00008, 0.64, 0.010, 0.62, 45.0, 74.0, 0.0040, -0.0082, 0.0013, 0.0040),
]


def class_name(variant: Variant) -> str:
    safe = "".join(part.title() for part in variant.name.split("_"))
    return f"IbkrMgcRocMomentumContinuation{safe}1MinV1"


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
    startup_candle_count = 280

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        high = dataframe["high"]
        low = dataframe["low"]
        prev_close = close.shift()
        tr = DataFrame({{"hl": high - low, "hc": (high - prev_close).abs(), "lc": (low - prev_close).abs()}}).max(axis=1)
        dataframe["atr"] = tr.rolling(14).mean()
        dataframe["ema21"] = close.ewm(span=21, adjust=False).mean()
        dataframe["ema55"] = close.ewm(span=55, adjust=False).mean()
        dataframe["ema144"] = close.ewm(span=144, adjust=False).mean()
        dataframe["roc"] = close.pct_change({variant.roc_period})
        dataframe["roc_slope"] = dataframe["roc"] - dataframe["roc"].shift(5)
        dataframe["ema_slope_atr"] = (dataframe["ema21"] - dataframe["ema21"].shift(12)) / dataframe["atr"].replace(0, 1)
        dataframe["pullback_atr"] = (close - dataframe["ema21"]).abs() / dataframe["atr"].replace(0, 1)
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
        trend_ok = (dataframe["ema21"] >= dataframe["ema55"] - dataframe["atr"] * 0.08) & (dataframe["close"] >= dataframe["ema144"] - dataframe["atr"] * 0.35)
        signal = (
            dataframe["entry_window"]
            & (dataframe["roc"].fillna(0) >= {variant.roc_min})
            & (dataframe["roc_slope"].fillna(0) >= {variant.roc_slope_min})
            & (dataframe["ema_slope_atr"].fillna(0) >= {variant.ema_slope_min})
            & (dataframe["pullback_atr"] <= {variant.pullback_atr_max})
            & (dataframe["rvol"] >= {variant.rvol_min})
            & dataframe["rsi14"].between({variant.rsi_min}, {variant.rsi_max})
            & trend_ok
        )
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{tag}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        momentum_lost = (dataframe["roc_slope"] < -0.00035) | (dataframe["roc"] < -0.00025)
        trend_lost = dataframe["close"] < dataframe["ema21"] - dataframe["atr"] * 0.55
        dataframe.loc[dataframe["force_exit_window"] | momentum_lost | trend_lost, "exit_long"] = 1
        return dataframe
'''


def write_materials(data_path: Path) -> list[Path]:
    materials: list[Path] = []
    for variant in base.VARIANTS:
        klass = class_name(variant)
        strategy = base.ROOT / "agent-material" / f"{klass}.py"
        strategy.write_text(strategy_source(klass, variant), encoding="utf-8")
        material = base.ROOT / "agent-material" / f"ibkr_mgc_roc_momentum_continuation_{variant.name}_1m_7d_v1.material.json"
        payload = {
            "package_id": f"ibkr-mgc-roc-momentum-continuation-{variant.name.replace('_', '-')}-1m-7d-v1",
            "title": f"IBKR MGC ROC momentum continuation {variant.name} 1m 7D",
            "symbol": "MGC",
            "timeframe": "1m",
            "timerange": base.timerange(data_path),
            "direction": "long",
            "data_path": str(data_path),
            "strategy_source_path": str(strategy),
            "strategy_class_name": klass,
            "strategy_brief": "Classic Rate of Change / ROC momentum-continuation family on retained real IBKR MGC 1m futures data; public-family precious-metals lane distinct from VWAP, RSI, RVOL, Turtle Soup, FRAMA, SMI, Vortex, pivots, PSAR, and Choppiness rows.",
            "evaluation_priority": ["public_family_diversity", "roc_momentum", "exact_1m_cost_density", "precious_metals_provider_parity"],
            "consumer_evidence_profile": {
                "branch_path": base.BRANCH_PATH,
                "regime_profit_branch_path": base.BRANCH_PATH,
                "branch_id": base.FACTOR_ID,
                "market": "FUTURES",
                "product": "precious_metals",
                "root_symbol": "MGC",
                "root_timeframe": "1m",
                "main_regime": "MomentumContinuation",
                "sub_regime": "RateOfChangeMomentum",
                "sub_sub_regime_or_profit_factor": base.FACTOR_ID,
                "profit_factor": base.FACTOR_ID,
                "base_timeframe": "1m",
                "training_timeframe": "1m",
                "material_timeframe": "1m",
                "provider": "IBKR",
                "provider_window": "7 D",
                "provider_provenance": f"IBKR FUT MGC 202606 1m 7 D retained source={base.SOURCE_ROOT.name}",
                "source_backed_family": "Rate of Change / ROC momentum continuation",
                "asset_class": "futures",
                "sec_type": "FUT",
                "exchange": "COMEX",
                "multiplier": "10",
                "last_trade_date": "202606",
                "gate_id": "Gate1IbkrMgcRocMomentumContinuation1m7d",
                "promotion_allowed": False,
                "trade_usable": False,
                "update_goal": False,
            },
            "notes": ["public_family=rate_of_change_momentum", "local_cache_replay=false_retained_real_ibkr_same_session", "downstream_forbidden_until_cost_density_survives"],
        }
        material.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        materials.append(material)
    return materials


base.class_name = class_name
base.label_for = label_for
base.strategy_source = strategy_source
base.write_materials = write_materials


if __name__ == "__main__":
    claim = Path("/tmp/ict-engine-agent-claims/board-b-factor-refinement") / f"{STAMP}-codex-ibkr-mgc1m-roc-momentum-continuation-7d-gate1-v1.claim"
    claim.parent.mkdir(parents=True, exist_ok=True)
    claim.write_text(
        f"task={base.FACTOR_ID}\nrun_root={base.ROOT}\nbranch_path={base.BRANCH_PATH}\n"
        "non_takeover=fresh MGC/1m Rate of Change momentum public-family Gate 1; collision scan found no exact MGC ROC board row or claim; avoids active SI/M2K repairs and cooled MGC SMI/FRAMA/VWAP/RSI/RVOL/adaptive/pivot rows\n",
        encoding="utf-8",
    )
    raise SystemExit(base.main())
