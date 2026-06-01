#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import shutil
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
base.ROOT = base.BASE / "runs" / f"{STAMP}-codex-ibkr-mgc1m-ulcer-risk-pressure-rebound-7d-gate1-v1"
base.SOURCE_ROOT = base.BASE / "runs/20260519T232924+0800-codex-ibkr-mgc1m-opening-vwap-rvol-reclaim-7d-gate1-v1"
base.SOURCE_DATA = base.SOURCE_ROOT / "data/provider/normalized/ibkr_mgc_202606_1m_7d.csv"
base.AQ_SYMBOL = "IBKR_MGC1M_ULCER_RISK_PRESSURE_REBOUND_7D_GATE1_V1"
base.FACTOR_ID = "ibkr_mgc1m_ulcer_risk_pressure_rebound_7d_gate1_v1"
base.BRANCH_PATH = "RiskPressureReversal -> UlcerIndexRebound -> ibkr_mgc1m_ulcer_risk_pressure_rebound_7d_gate1_v1"
base.SOURCE_BACKED_FAMILY = "Ulcer Index / risk-pressure rebound"
base.SUMMARY_TABLE_TITLE = "Exact MGC 1m Ulcer Index risk-pressure rebound rows:"

base.VARIANTS = [
    base.Variant("ulcer_dense", 14, 0.018, -0.004, 0.35, -0.040, 1.40, 0.0024, -0.0060, 0.0008, 0.0024),
    base.Variant("ulcer_balanced", 21, 0.028, -0.001, 0.45, -0.025, 1.15, 0.0032, -0.0075, 0.0010, 0.0032),
    base.Variant("ulcer_quality", 28, 0.040, 0.002, 0.55, -0.010, 0.95, 0.0045, -0.0095, 0.0014, 0.0045),
    base.Variant("ulcer_capitulation", 21, 0.055, -0.006, 0.40, -0.055, 1.65, 0.0038, -0.0105, 0.0012, 0.0038),
]


def class_name(variant: base.Variant) -> str:
    safe = "".join(part.title() for part in variant.name.split("_"))
    return f"IbkrMgcUlcerRiskPressureRebound{safe}1MinV1"


def label_for(row: dict) -> str:
    package = str(row.get("package_id") or "")
    variant = next((item.name for item in base.VARIANTS if item.name.replace("_", "-") in package), "unknown")
    return f"MGC/{variant}/1m"


def strategy_source(name: str, variant: base.Variant) -> str:
    tag = f"{base.FACTOR_ID}_{variant.name}"
    return f'''from freqtrade.strategy import IStrategy
from pandas import DataFrame
import numpy as np


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
        period = {variant.vi_period}
        roll_max = close.rolling(period).max()
        drawdown_pct = ((close / roll_max.replace(0, np.nan)) - 1.0) * 100.0
        dataframe["ulcer_index"] = np.sqrt((drawdown_pct.pow(2)).rolling(period).mean())
        dataframe["ulcer_delta"] = dataframe["ulcer_index"] - dataframe["ulcer_index"].shift(5)
        dataframe["drawdown_atr"] = (roll_max - close) / dataframe["atr"].replace(0, 1)
        dataframe["ema13"] = close.ewm(span=13, adjust=False).mean()
        dataframe["ema34"] = close.ewm(span=34, adjust=False).mean()
        dataframe["ema89"] = close.ewm(span=89, adjust=False).mean()
        dataframe["ema_slope_atr"] = (dataframe["ema13"] - dataframe["ema13"].shift(8)) / dataframe["atr"].replace(0, 1)
        dataframe["rebound_atr"] = (close - close.rolling(8).min()) / dataframe["atr"].replace(0, 1)
        dataframe["close_position"] = (close - low.rolling(8).min()) / (high.rolling(8).max() - low.rolling(8).min()).replace(0, np.nan)
        dataframe["rvol"] = dataframe["volume"] / dataframe["volume"].rolling(60).mean().replace(0, 1)
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean().replace(0, 1e-9)
        dataframe["rsi14"] = 100.0 - (100.0 / (1.0 + gain / loss))
        minute = dataframe["date"].dt.hour * 60 + dataframe["date"].dt.minute
        dataframe["entry_window"] = ((minute >= 13 * 60 + 35) & (minute <= 20 * 60 + 40)) | ((minute >= 0) & (minute <= 2 * 60 + 15))
        dataframe["force_exit_window"] = (minute >= 20 * 60 + 50) & (minute < 21 * 60 + 55)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        pressure_washout = (
            (dataframe["ulcer_index"] >= {variant.vi_spread_min * 100.0})
            & (dataframe["drawdown_atr"] >= {variant.pullback_atr_max * 0.55})
            & (dataframe["close"] <= dataframe["ema89"] + dataframe["atr"] * 0.35)
        )
        rebound_signal = (
            (dataframe["close"] > dataframe["ema13"])
            | ((dataframe["rebound_atr"] >= {max(0.25, variant.vi_spread_min * 8.0)}) & (dataframe["close_position"] >= 0.55))
        )
        signal = (
            dataframe["entry_window"]
            & pressure_washout
            & rebound_signal
            & (dataframe["ulcer_delta"].fillna(0) <= {variant.vi_slope_min * 100.0})
            & (dataframe["ema_slope_atr"].fillna(0) >= {variant.ema_slope_min})
            & (dataframe["rvol"] >= {variant.rvol_min})
            & dataframe["rsi14"].between(24, 68)
        )
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{tag}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        pressure_return = (dataframe["close"] < dataframe["ema13"] - dataframe["atr"] * 0.45) & (dataframe["ulcer_delta"] > 0)
        rebound_faded = (dataframe["rsi14"] < 35) | (dataframe["close_position"] < 0.25)
        dataframe.loc[dataframe["force_exit_window"] | pressure_return | rebound_faded, "exit_long"] = 1
        return dataframe
'''


def write_materials(data_path: Path) -> list[Path]:
    materials: list[Path] = []
    for variant in base.VARIANTS:
        klass = class_name(variant)
        strategy = base.ROOT / "agent-material" / f"{klass}.py"
        strategy.write_text(strategy_source(klass, variant), encoding="utf-8")
        material = base.ROOT / "agent-material" / f"ibkr_mgc_ulcer_risk_pressure_rebound_{variant.name}_1m_7d_v1.material.json"
        payload = {
            "package_id": f"ibkr-mgc-ulcer-risk-pressure-rebound-{variant.name.replace('_', '-')}-1m-7d-v1",
            "title": f"IBKR MGC Ulcer Index risk-pressure rebound {variant.name} 1m 7D",
            "symbol": "MGC",
            "timeframe": "1m",
            "timerange": base.timerange(data_path),
            "direction": "long",
            "data_path": str(data_path),
            "strategy_source_path": str(strategy),
            "strategy_class_name": klass,
            "strategy_brief": "Public Ulcer Index drawdown-pressure rebound family on retained real IBKR MGC 1m futures data; risk-pressure reversal lane distinct from VWAP, RSI, RVOL, liquidity sweep, pivots, trend channels, and microtrend families.",
            "evaluation_priority": ["public_family_diversity", "exact_1m_cost_density", "precious_metals_risk_pressure_reversal"],
            "consumer_evidence_profile": {
                "branch_path": base.BRANCH_PATH,
                "regime_profit_branch_path": base.BRANCH_PATH,
                "branch_id": base.FACTOR_ID,
                "market": "FUTURES",
                "product": "precious_metals",
                "root_symbol": "MGC",
                "root_timeframe": "1m",
                "main_regime": "RiskPressureReversal",
                "sub_regime": "UlcerIndexRebound",
                "sub_sub_regime_or_profit_factor": base.FACTOR_ID,
                "profit_factor": base.FACTOR_ID,
                "base_timeframe": "1m",
                "training_timeframe": "1m",
                "material_timeframe": "1m",
                "provider": "IBKR",
                "provider_window": "7 D",
                "provider_provenance": f"IBKR FUT MGC 202606 1m 7 D retained source={base.SOURCE_ROOT.name}",
                "source_backed_family": "Ulcer Index / risk-pressure rebound",
                "asset_class": "futures",
                "sec_type": "FUT",
                "exchange": "COMEX",
                "multiplier": "10",
                "last_trade_date": "202606",
                "gate_id": "Gate1IbkrMgcUlcerRiskPressureRebound1m7d",
                "promotion_allowed": False,
                "trade_usable": False,
                "update_goal": False,
            },
            "notes": ["public_family=ulcer_index", "local_cache_replay=false_source_provider_root_reused", "downstream_forbidden_until_cost_density_survives"],
        }
        material.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        materials.append(material)
    return materials


def main() -> int:
    for sub in ["data/provider/normalized", "agent-material", "summaries", "checks", "command-output", "state", "scripts", "materials"]:
        (base.ROOT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(__file__, base.ROOT / "scripts" / Path(__file__).name)
    (base.ROOT / "materials/source_manifest.json").write_text(json.dumps([
        {"source": "public Ulcer Index / Ulcer Performance Index drawdown-risk pressure family", "use": "1m risk-pressure rebound diversity Gate 1"},
        {"source": "retained IBKR MGC 202606 1m 7 D provider packet", "path": str(base.SOURCE_DATA)},
    ], indent=2) + "\n", encoding="utf-8")
    if not base.SOURCE_DATA.exists():
        raise FileNotFoundError(base.SOURCE_DATA)
    data_path = base.ROOT / "data/provider/normalized/ibkr_mgc_202606_1m_7d.csv"
    shutil.copy2(base.SOURCE_DATA, data_path)
    provider_rows = [{
        "provider": "IBKR", "sec_type": "FUT", "symbol": "MGC", "product": "precious_metals", "exchange": "COMEX",
        "last_trade_date": "202606", "timeframe": "1m", "duration": "7 D", "rows": base.row_count(data_path),
        "path": str(data_path), "source_provider_root": str(base.SOURCE_ROOT), "local_cache_replay": "false_retained_real_ibkr_same_session",
    }]
    with (base.ROOT / "summaries/provider_provenance_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(provider_rows[0].keys()))
        writer.writeheader(); writer.writerows(provider_rows)
    materials = write_materials(data_path)
    strategies = [Path(json.loads(path.read_text())["strategy_source_path"]) for path in materials]
    commands = [base.run_cmd("00_strategy_py_compile", [base.PY, "-m", "py_compile", *strategies], timeout=120)]
    if commands[-1]["exit"] == 0:
        args: list[object] = [base.ICT, "auto-quant-agent-material-batch", "--symbol", base.AQ_SYMBOL, "--state-dir", base.ROOT / "state", "--max-parallel", "1"]
        if base.AQ_REPO.exists():
            args += ["--repo-url", base.AQ_REPO]
        for material in materials:
            args += ["--material", material]
        commands.append(base.run_cmd("01_auto_quant_agent_material_batch", args, timeout=900))
    if commands[-1]["exit"] == 0:
        commands.append(base.run_cmd("02_auto_quant_agent_material_dispatch", [base.ICT, "auto-quant-agent-material-dispatch", "--symbol", base.AQ_SYMBOL, "--state-dir", base.ROOT / "state"], timeout=1200))
    if commands[-1]["exit"] == 0:
        commands.append(base.run_cmd("03_auto_quant_agent_material_rank", [base.ICT, "auto-quant-agent-material-rank", "--symbol", base.AQ_SYMBOL, "--state-dir", base.ROOT / "state"], timeout=240))

    rank_rows = base.latest_rank_rows() if commands[-1]["name"] == "03_auto_quant_agent_material_rank" and commands[-1]["exit"] == 0 else []
    representative_price = base.cost_model.representative_price_from_provider_rows(provider_rows)
    cost_summary = base.cost_model.rank_rows_real_fee_summary(
        rank_rows,
        symbol=base.ROOT_SYMBOL,
        representative_price=representative_price,
        label_fn=label_for,
    )
    cost_rows = cost_summary["rows"]
    survivors_instrument_cost = cost_summary["survivors"]
    branch_paths = sorted({str(row.get("branch_path") or "") for row in rank_rows})
    branch_ok = bool(rank_rows) and branch_paths == [base.BRANCH_PATH]
    downstream = base.hard_gate_downstream_allowed(branch_ok, survivors_instrument_cost)
    decision = "gate1_ibkr_mgc1m_ulcer_risk_pressure_rebound_downstream_allowed" if downstream else "drop_or_block_gate1_practical"
    metrics = {
        "run_root": str(base.ROOT), "source_provider_root": str(base.SOURCE_ROOT), "factor_id": base.FACTOR_ID,
        "branch_path": base.BRANCH_PATH, "decision": decision, "source_backed_family": base.SOURCE_BACKED_FAMILY,
        "provider_rows": provider_rows, "rank_rows": len(rank_rows),
        "rank_total_trade_count": sum(int(row.get("trade_count") or 0) for row in rank_rows),
        "representative_price": representative_price,
        "cost_model": cost_summary["cost_model"],
        "promotion_cost_verified": cost_summary["promotion_cost_verified"],
        "exact_1m_instrument_cost_rows": cost_rows,
        "exact_1m_survivors_instrument_cost": survivors_instrument_cost,
        "branch_paths": branch_paths, "branch_fields_preserved": branch_ok, "downstream_allowed": downstream,
        "pre_bayes_allowed": downstream, "bbn_allowed": downstream, "catboost_allowed": downstream, "execution_tree_allowed": downstream,
        "promotion_allowed": False, "trade_usable": False, "update_goal": False, "local_cache_replay": False,
        "command_exits": {cmd["name"]: cmd["exit"] for cmd in commands}, "skill_update": "needed_after_downstream" if downstream else "not_needed",
    }
    (base.ROOT / "checks/terminal_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    base.cost_model.write_real_fee_rank_rows_csv(base.ROOT / "summaries/rank_rows.csv", cost_rows)
    lines = base.cost_model.real_fee_rank_table_lines(
        decision=decision,
        title="Source: public Ulcer Index drawdown/risk-pressure rebound family; rewritten as Freqtrade/AQ material.",
        rows=cost_rows,
        branch_ok=branch_ok,
        survivors=survivors_instrument_cost,
        downstream=downstream,
    )
    (base.ROOT / "summaries/terminal_decision_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0 if commands and commands[-1]["name"] == "03_auto_quant_agent_material_rank" and commands[-1]["exit"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
