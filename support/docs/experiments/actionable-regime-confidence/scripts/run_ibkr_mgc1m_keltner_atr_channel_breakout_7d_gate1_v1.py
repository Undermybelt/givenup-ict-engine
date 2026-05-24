#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path


SCRIPT = Path(__file__).resolve()
BASE_SCRIPT = SCRIPT.with_name("run_ibkr_mgc1m_donchian_turtle_breakout_7d_gate1_v1.py")
spec = importlib.util.spec_from_file_location("mgc_donchian_gate1_template", BASE_SCRIPT)
base = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = base
spec.loader.exec_module(base)

base.ROOT = base.BASE / "runs" / f"{base.STAMP}-codex-ibkr-mgc1m-keltner-atr-channel-breakout-7d-gate1-v1"
base.AQ_SYMBOL = "IBKR_MGC1M_KELTNER_ATR_CHANNEL_BREAKOUT_7D_GATE1_V1"
base.FACTOR_ID = "ibkr_mgc1m_keltner_atr_channel_breakout_7d_gate1_v1"
base.BRANCH_PATH = "TrendExpansion -> KeltnerAtrChannelBreakout -> ibkr_mgc1m_keltner_atr_channel_breakout_7d_gate1_v1"


@dataclass(frozen=True)
class Variant:
    name: str
    atr_mult: float
    rvol_min: float
    trend_mode: str
    entry_mode: str
    roi: float
    stoploss: float
    trail: float
    offset: float
    startup: int


base.VARIANTS = [
    Variant("dense_upper20", 1.15, 0.60, "ema20gt50", "upper_cross", 0.0030, -0.0070, 0.0010, 0.0028, 240),
    Variant("balanced_upper20", 1.45, 0.75, "ema20gt50", "upper_cross", 0.0042, -0.0090, 0.0014, 0.0038, 260),
    Variant("trend_upper20", 1.75, 0.70, "ema20gt50gt200", "upper_cross", 0.0055, -0.0110, 0.0018, 0.0050, 320),
    Variant("mid_reclaim", 1.30, 0.55, "closegtvwap", "mid_reclaim", 0.0032, -0.0075, 0.0011, 0.0030, 240),
]


def class_name(variant: Variant) -> str:
    safe = "".join(part.title() for part in variant.name.split("_"))
    return f"IbkrMgcKeltnerAtrChannelBreakout{safe}1MinV1"


def strategy_source(name: str, variant: Variant) -> str:
    tag = f"{base.FACTOR_ID}_{variant.name}"
    trend_expr = {
        "ema20gt50": '(dataframe["ema20"] > dataframe["ema50"]) & (dataframe["close"] > dataframe["ema20"])',
        "ema20gt50gt200": '((dataframe["ema20"] > dataframe["ema50"]) & (dataframe["ema50"] > dataframe["ema200"]) & (dataframe["close"] > dataframe["ema20"]))',
        "closegtvwap": '(dataframe["close"] > dataframe["session_vwap"]) & (dataframe["ema20"] >= dataframe["ema50"] - dataframe["atr14"] * 0.08)',
    }[variant.trend_mode]
    entry_expr = {
        "upper_cross": '((dataframe["close"] > dataframe["kelt_upper"]) & (dataframe["close"].shift(1) <= dataframe["kelt_upper"].shift(1)))',
        "mid_reclaim": '((dataframe["low"].rolling(8).min() <= dataframe["kelt_mid"]) & (dataframe["close"] > dataframe["kelt_mid"]) & (dataframe["close"] > dataframe["ema20"]))',
    }[variant.entry_mode]
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
    startup_candle_count = {variant.startup}

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = dataframe["close"].ewm(span=20, adjust=False).mean()
        dataframe["ema50"] = dataframe["close"].ewm(span=50, adjust=False).mean()
        dataframe["ema200"] = dataframe["close"].ewm(span=200, adjust=False).mean()
        tr = DataFrame({{"hl": dataframe["high"] - dataframe["low"], "hc": (dataframe["high"] - dataframe["close"].shift()).abs(), "lc": (dataframe["low"] - dataframe["close"].shift()).abs()}}).max(axis=1)
        dataframe["atr14"] = tr.rolling(14).mean()
        dataframe["atr50"] = tr.rolling(50).mean()
        dataframe["kelt_mid"] = dataframe["close"].ewm(span=20, adjust=False).mean()
        dataframe["kelt_upper"] = dataframe["kelt_mid"] + dataframe["atr14"] * {variant.atr_mult}
        dataframe["kelt_lower"] = dataframe["kelt_mid"] - dataframe["atr14"] * {variant.atr_mult}
        dataframe["vol60"] = dataframe["volume"].rolling(60).mean()
        dataframe["rvol"] = dataframe["volume"] / dataframe["vol60"].replace(0, 1)
        dataframe["atr_pct"] = dataframe["atr14"] / dataframe["close"]
        dataframe["atr_regime"] = dataframe["atr14"] / dataframe["atr50"].replace(0, 0.000001)
        dataframe["ema20_slope_atr"] = (dataframe["ema20"] - dataframe["ema20"].shift(10)) / dataframe["atr14"].replace(0, 0.000001)
        dataframe["close_pos"] = (dataframe["close"] - dataframe["low"]) / dataframe["high"].sub(dataframe["low"]).replace(0, 1)
        dt = dataframe["date"]
        day_key = dt.dt.strftime("%Y-%m-%d")
        typical = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3.0
        pv = typical * dataframe["volume"]
        dataframe["session_vwap"] = pv.groupby(day_key).cumsum() / dataframe["volume"].groupby(day_key).cumsum().replace(0, 1)
        minute = dt.dt.hour * 60 + dt.dt.minute
        dataframe["entry_window"] = ((minute >= 0) & (minute <= 2 * 60 + 30)) | ((minute >= 13 * 60 + 30) & (minute <= 20 * 60 + 30))
        dataframe["force_exit_window"] = (minute >= 20 * 60 + 50) & (minute < 21 * 60 + 55)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        entry = {entry_expr}
        signal = (
            dataframe["entry_window"]
            & entry
            & ({trend_expr})
            & dataframe["atr_pct"].between(0.00020, 0.0120)
            & dataframe["atr_regime"].between(0.50, 2.40)
            & (dataframe["rvol"] >= {variant.rvol_min})
            & (dataframe["ema20_slope_atr"].fillna(0) >= -0.04)
            & (dataframe["close_pos"].fillna(0.5) >= 0.45)
        )
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{tag}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        fail = (dataframe["close"] < dataframe["kelt_mid"] - dataframe["atr14"] * 0.30) | (dataframe["close"] < dataframe["ema50"] - dataframe["atr14"] * 0.20)
        dataframe.loc[dataframe["force_exit_window"] | fail, "exit_long"] = 1
        return dataframe
'''


def label_for(row: dict) -> str:
    package = str(row.get("package_id") or "")
    variant = next((item.name for item in base.VARIANTS if item.name.replace("_", "-") in package), "unknown")
    return f"MGC/{variant}/1m"


def write_materials(data_path: Path) -> list[Path]:
    materials: list[Path] = []
    for variant in base.VARIANTS:
        klass = class_name(variant)
        strategy = base.ROOT / "agent-material" / f"{klass}.py"
        strategy.write_text(strategy_source(klass, variant), encoding="utf-8")
        material = base.ROOT / "agent-material" / f"ibkr_mgc_keltner_atr_channel_breakout_{variant.name}_1m_7d_v1.material.json"
        payload = {
            "package_id": f"ibkr-mgc-keltner-atr-channel-breakout-{variant.name.replace('_', '-')}-1m-7d-v1",
            "title": f"IBKR MGC Keltner/ATR channel breakout {variant.name} 1m 7D",
            "symbol": "MGC",
            "timeframe": "1m",
            "timerange": base.timerange(data_path),
            "direction": "long",
            "data_path": str(data_path),
            "strategy_source_path": str(strategy),
            "strategy_class_name": klass,
            "strategy_brief": "Public Keltner/ATR channel breakout on MGC 1m real IBKR futures data; distinct from Donchian, RSI/VWAP, and micro-trend families.",
            "evaluation_priority": ["source_backed_diversity", "exact_1m_cost_density", "precious_metals_provider_parity"],
            "consumer_evidence_profile": {
                "branch_path": base.BRANCH_PATH,
                "regime_profit_branch_path": base.BRANCH_PATH,
                "branch_id": base.FACTOR_ID,
                "market": "FUTURES",
                "product": "precious_metals",
                "root_symbol": "MGC",
                "root_timeframe": "1m",
                "main_regime": "TrendExpansion",
                "sub_regime": "KeltnerAtrChannelBreakout",
                "sub_sub_regime_or_profit_factor": base.FACTOR_ID,
                "profit_factor": base.FACTOR_ID,
                "base_timeframe": "1m",
                "training_timeframe": "1m",
                "material_timeframe": "1m",
                "provider": "IBKR",
                "provider_window": "7 D",
                "provider_provenance": f"IBKR FUT MGC 202606 1m 7 D source={base.SOURCE_ROOT.name}",
                "source_backed_family": "Keltner/ATR channel breakout",
                "asset_class": "futures",
                "sec_type": "FUT",
                "exchange": "COMEX",
                "multiplier": "10",
                "last_trade_date": "202606",
                "gate_id": "Gate1IbkrMgcKeltnerAtrChannelBreakout1m7d",
                "promotion_allowed": False,
                "trade_usable": False,
                "update_goal": False,
            },
            "notes": ["source_backed=keltner_atr_channel_breakout", "local_cache_replay=false_source_provider_root_reused", "downstream_forbidden_until_cost_density_survives"],
        }
        material.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        materials.append(material)
    return materials


base.class_name = class_name
base.strategy_source = strategy_source
base.label_for = label_for
base.write_materials = write_materials


def main() -> int:
    rc = base.main()
    metrics_path = base.ROOT / "checks/terminal_metrics.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        metrics["factor_id"] = base.FACTOR_ID
        metrics["branch_path"] = base.BRANCH_PATH
        metrics["source_backed_family"] = "Keltner/ATR channel breakout"
        if metrics.get("decision") == "gate1_ibkr_mgc1m_donchian_turtle_downstream_allowed":
            metrics["decision"] = "gate1_ibkr_mgc1m_keltner_atr_channel_breakout_downstream_allowed"
        metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    summary_path = base.ROOT / "summaries/terminal_decision_summary.md"
    if summary_path.exists():
        text = summary_path.read_text(encoding="utf-8")
        text = text.replace("gate1_ibkr_mgc1m_donchian_turtle_downstream_allowed", "gate1_ibkr_mgc1m_keltner_atr_channel_breakout_downstream_allowed")
        text = text.replace("Exact MGC 1m Donchian/Turtle rows:", "Exact MGC 1m Keltner/ATR channel-breakout rows:")
        text += "\n- source-backed family: `Keltner/ATR channel breakout`\n"
        summary_path.write_text(text, encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
