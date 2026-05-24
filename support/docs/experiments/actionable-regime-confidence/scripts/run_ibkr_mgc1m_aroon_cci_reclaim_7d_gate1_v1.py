#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


SCRIPT = Path(__file__).resolve()
TEMPLATE = SCRIPT.with_name("run_ibkr_mgc1m_williams_mfi_reclaim_7d_gate1_v1.py")
spec = importlib.util.spec_from_file_location("mgc_williams_mfi_template", TEMPLATE)
template = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = template
spec.loader.exec_module(template)

STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
template.ROOT = template.BASE / "runs" / f"{STAMP}-codex-ibkr-mgc1m-aroon-cci-reclaim-7d-gate1-v1"
template.AQ_SYMBOL = "IBKR_MGC1M_AROON_CCI_RECLAIM_7D_GATE1_V1"
template.FACTOR_ID = "ibkr_mgc1m_aroon_cci_reclaim_7d_gate1_v1"
template.BRANCH_PATH = "TrendExpansion -> AroonCciReclaim -> AroonCciReclaim -> ibkr_mgc1m_aroon_cci_reclaim_7d_gate1_v1"


@dataclass(frozen=True)
class Variant:
    name: str
    aroon_up_min: float
    aroon_margin_min: float
    cci_min: float
    cci_cross: float
    rvol_min: float
    pullback_atr: float
    roi: float
    stoploss: float
    trail: float
    offset: float


template.VARIANTS = [
    Variant("aroon_cci_dense", 56.0, -8.0, -120.0, -75.0, 0.35, 0.45, 0.0019, -0.0048, 0.0007, 0.0019),
    Variant("aroon_cci_balanced", 64.0, 2.0, -95.0, -45.0, 0.45, 0.36, 0.0028, -0.0062, 0.0009, 0.0029),
    Variant("aroon_cci_quality", 72.0, 12.0, -70.0, -15.0, 0.58, 0.28, 0.0038, -0.0078, 0.0012, 0.0039),
    Variant("aroon_cci_breakout", 80.0, 20.0, -35.0, 0.0, 0.70, 0.18, 0.0045, -0.0090, 0.0014, 0.0046),
]


def class_name(variant: Variant) -> str:
    safe = "".join(part.title() for part in variant.name.split("_"))
    return f"IbkrMgcAroonCciReclaim{safe}1MinV1"


def strategy_source(name: str, variant: Variant) -> str:
    tag = f"{template.FACTOR_ID}_{variant.name}"
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
        dataframe["ema21"] = close.ewm(span=21, adjust=False).mean()
        dataframe["ema89"] = close.ewm(span=89, adjust=False).mean()
        tr = DataFrame({{"hl": high - low, "hc": (high - close.shift()).abs(), "lc": (low - close.shift()).abs()}}).max(axis=1)
        dataframe["atr14"] = tr.rolling(14).mean()
        typical = (high + low + close) / 3.0
        tp_mean = typical.rolling(20).mean()
        mean_dev = (typical - tp_mean).abs().rolling(20).mean().replace(0, 1e-9)
        dataframe["cci20"] = (typical - tp_mean) / (0.015 * mean_dev)
        dataframe["aroon_up"] = high.rolling(25).apply(lambda x: 100.0 * (25 - 1 - x.argmax()) / 25, raw=True)
        dataframe["aroon_down"] = low.rolling(25).apply(lambda x: 100.0 * (25 - 1 - x.argmin()) / 25, raw=True)
        dataframe["aroon_margin"] = dataframe["aroon_up"] - dataframe["aroon_down"]
        dataframe["vol60"] = dataframe["volume"].rolling(60).mean()
        dataframe["rvol"] = dataframe["volume"] / dataframe["vol60"].replace(0, 1)
        dataframe["pullback_atr"] = (dataframe["ema21"] - close) / dataframe["atr14"].replace(0, 1)
        dataframe["prior_high"] = high.shift(1).rolling(18).max()
        dataframe["prior_low"] = low.shift(1).rolling(18).min()
        minute = dataframe["date"].dt.hour * 60 + dataframe["date"].dt.minute
        dataframe["entry_window"] = ((minute >= 0) & (minute <= 2 * 60 + 20)) | ((minute >= 13 * 60 + 35) & (minute <= 20 * 60 + 20))
        dataframe["force_exit_window"] = (minute >= 20 * 60 + 50) & (minute < 21 * 60 + 55)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        aroon_ok = (dataframe["aroon_up"] >= {variant.aroon_up_min}) & (dataframe["aroon_margin"] >= {variant.aroon_margin_min})
        cci_reclaim = (dataframe["cci20"] >= {variant.cci_min}) & (dataframe["cci20"] > dataframe["cci20"].shift(1)) & (dataframe["cci20"].shift(1) <= {variant.cci_cross})
        trend_guard = dataframe["close"] > dataframe["ema89"] - dataframe["atr14"] * 1.10
        pullback_ok = dataframe["pullback_atr"].between(-0.35, {variant.pullback_atr})
        structure_ok = (dataframe["close"] > dataframe["prior_low"] + dataframe["atr14"] * 0.08) | (dataframe["close"] > dataframe["prior_high"] - dataframe["atr14"] * 0.25)
        signal = dataframe["entry_window"] & aroon_ok & cci_reclaim & trend_guard & pullback_ok & structure_ok & (dataframe["rvol"] >= {variant.rvol_min})
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{tag}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        failed = (dataframe["aroon_margin"] < -15) | (dataframe["close"] < dataframe["prior_low"] - dataframe["atr14"] * 0.25)
        exhausted = (dataframe["cci20"] > 160) | (dataframe["close"] > dataframe["ema21"] + dataframe["atr14"] * 0.60)
        dataframe.loc[dataframe["force_exit_window"] | failed | exhausted, "exit_long"] = 1
        return dataframe
'''


def label_for(row: dict) -> str:
    package = str(row.get("package_id") or "")
    variant = next((item.name for item in template.VARIANTS if item.name.replace("_", "-") in package), "unknown")
    return f"MGC/{variant}/1m"


def write_materials(data_path: Path) -> list[Path]:
    materials: list[Path] = []
    for variant in template.VARIANTS:
        klass = class_name(variant)
        strategy = template.ROOT / "agent-material" / f"{klass}.py"
        strategy.write_text(strategy_source(klass, variant), encoding="utf-8")
        material = template.ROOT / "agent-material" / f"ibkr_mgc_aroon_cci_reclaim_{variant.name}_1m_7d_v1.material.json"
        payload = {
            "package_id": f"ibkr-mgc-aroon-cci-reclaim-{variant.name.replace('_', '-')}-1m-7d-v1",
            "title": f"IBKR MGC Aroon CCI reclaim {variant.name} 1m 7D",
            "symbol": "MGC",
            "timeframe": "1m",
            "timerange": template.timerange(data_path),
            "direction": "long",
            "data_path": str(data_path),
            "strategy_source_path": str(strategy),
            "strategy_class_name": klass,
            "strategy_brief": "Public Aroon trend-strength plus Commodity Channel Index reclaim on MGC 1m real IBKR futures data; classic oscillator/trend hybrid diversity candidate.",
            "evaluation_priority": ["source_backed_diversity", "exact_1m_cost_density", "precious_metals_provider_parity"],
            "consumer_evidence_profile": {
                "branch_path": template.BRANCH_PATH,
                "regime_profit_branch_path": template.BRANCH_PATH,
                "branch_id": template.FACTOR_ID,
                "market": "FUTURES",
                "product": "precious_metals",
                "root_symbol": "MGC",
                "root_timeframe": "1m",
                "main_regime": "TrendExpansion",
                "sub_regime": "AroonCciReclaim",
                "sub_sub_regime_or_profit_factor": "AroonCciReclaim",
                "profit_factor": template.FACTOR_ID,
                "profit_factor_id": template.FACTOR_ID,
                "base_timeframe": "1m",
                "training_timeframe": "1m",
                "material_timeframe": "1m",
                "provider": "IBKR",
                "provider_window": "7 D",
                "provider_provenance": f"IBKR FUT MGC 202606 1m 7 D source={template.SOURCE_ROOT.name}",
                "source_backed_family": "Aroon / CCI reclaim",
                "asset_class": "futures",
                "sec_type": "FUT",
                "exchange": "COMEX",
                "multiplier": "10",
                "last_trade_date": "202606",
                "gate_id": "Gate1IbkrMgcAroonCciReclaim1m7d",
                "promotion_allowed": False,
                "trade_usable": False,
                "update_goal": False,
            },
            "notes": ["source_backed=classic_aroon_cci", "local_cache_replay=false_source_provider_root_reused", "downstream_forbidden_until_cost_density_survives"],
        }
        material.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        materials.append(material)
    return materials


def main() -> int:
    template.class_name = class_name
    template.strategy_source = strategy_source
    template.label_for = label_for
    template.write_materials = write_materials
    rc = template.main()
    root = template.ROOT
    (root / "materials/source_manifest.json").write_text(json.dumps([
        {"source": "classic Aroon indicator and Commodity Channel Index strategy family", "use": "public/time-tested trend-strength plus CCI reclaim idea; no external runtime dependency"},
        {"source": "retained IBKR MGC 202606 1m 7 D provider packet", "path": str(template.SOURCE_DATA)},
    ], indent=2) + "\n", encoding="utf-8")
    summary_path = root / "summaries/terminal_decision_summary.md"
    if summary_path.exists():
        text = summary_path.read_text(encoding="utf-8")
        text = text.replace("Williams %R / MFI", "Aroon / CCI")
        text = text.replace("classic oscillator family", "classic trend-strength / CCI reclaim family")
        summary_path.write_text(text, encoding="utf-8")
    metrics_path = root / "checks/terminal_metrics.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        metrics["source"] = "classic Aroon and CCI strategy family; no external runtime dependency"
        metrics["branch_path"] = template.BRANCH_PATH
        metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
