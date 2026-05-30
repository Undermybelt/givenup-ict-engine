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
base.ROOT = base.BASE / "runs" / f"{STAMP}-codex-ibkr-mnq1m-qstick-body-momentum-7d-gate1-v1"
base.SOURCE_ROOT = base.BASE / "runs/20260526T114821+0800-codex-ibkr-futures-strict-trend-root-liquidity-sweep-vwap-reclaim-excursion-cap-1m-mtf-gate1-v1"
base.SOURCE_DATA = base.SOURCE_ROOT / "data/provider/normalized/ibkr_mnq_202606_1m_7d.csv"
base.AQ_SYMBOL = "IBKR_MNQ1M_QSTICK_BODY_MOMENTUM_7D_GATE1_V1"
base.FACTOR_ID = "ibkr_mnq1m_qstick_body_momentum_7d_gate1_v1"
base.BRANCH_PATH = "CandleBodyMomentum -> QstickBodyMomentum -> QstickBodyMomentum -> ibkr_mnq1m_qstick_body_momentum_7d_gate1_v1"

TIMEFRAME_SOURCES = {
    "1m": base.SOURCE_ROOT / "data/provider/normalized/ibkr_mnq_202606_1m_7d.csv",
    "5m": base.SOURCE_ROOT / "data/provider/normalized/ibkr_mnq_202606_5m_1m.csv",
    "15m": base.SOURCE_ROOT / "data/provider/normalized/ibkr_mnq_202606_15m_1m.csv",
    "30m": base.SOURCE_ROOT / "data/provider/normalized/ibkr_mnq_202606_30m_1m.csv",
    "1h": base.SOURCE_ROOT / "data/provider/normalized/ibkr_mnq_202606_1h_1m.csv",
    "4h": base.SOURCE_ROOT / "data/provider/normalized/ibkr_mnq_202606_4h_1m.csv",
    "1d": base.SOURCE_ROOT / "data/provider/normalized/ibkr_mnq_202606_1d_6m.csv",
}

base.VARIANTS = [
    base.Variant("qstick_dense", 8, 0.0009, 0.00015, 0.36, -0.020, 1.18, 0.0028, -0.0065, 0.0009, 0.0028),
    base.Variant("qstick_balanced", 13, 0.0014, 0.00025, 0.48, -0.006, 0.98, 0.0034, -0.0074, 0.0011, 0.0034),
    base.Variant("qstick_quality", 21, 0.0022, 0.00035, 0.62, 0.006, 0.82, 0.0048, -0.0088, 0.0015, 0.0048),
    base.Variant("qstick_reversal", 8, -0.0004, 0.00045, 0.42, -0.014, 1.06, 0.0030, -0.0068, 0.0010, 0.0030),
]


def timeframe_class_suffix(timeframe: str) -> str:
    return {
        "1m": "1Min",
        "5m": "5Min",
        "15m": "15Min",
        "30m": "30Min",
        "1h": "1Hour",
        "4h": "4Hour",
        "1d": "1Day",
    }.get(timeframe, "".join(part.title() for part in timeframe.split("_")))


def class_name(variant: base.Variant, timeframe: str = "1m") -> str:
    safe = "".join(part.title() for part in variant.name.split("_"))
    return f"IbkrMnqQstickBodyMomentum{safe}{timeframe_class_suffix(timeframe)}V1"


def label_for(row: dict) -> str:
    package = str(row.get("package_id") or "")
    variant = next((item.name for item in base.VARIANTS if item.name.replace("_", "-") in package), "unknown")
    timeframe = next((tf for tf in TIMEFRAME_SOURCES if f"-{tf}-" in package or f"_{tf}_" in package), str(row.get("timeframe") or "unknown"))
    return f"MNQ/{variant}/{timeframe}"


def score_rank_rows_with_instrument_cost(rank_rows: list[dict], *, representative_price: float) -> tuple[list[dict], list[str], bool]:
    summary = base.cost_model.rank_rows_real_fee_summary(
        rank_rows,
        symbol="MNQ",
        representative_price=representative_price,
        label_fn=label_for,
    )
    rows = list(summary["rows"])
    branch_ok = bool(rank_rows) and all(row.get("branch_path") == base.BRANCH_PATH for row in rows)
    return rows, list(summary["survivors"]), branch_ok


def strategy_source(name: str, variant: base.Variant, timeframe: str = "1m") -> str:
    tag = f"{base.FACTOR_ID}_{variant.name}"
    is_reversal = "reversal" in variant.name
    qstick_clause = (
        f'(dataframe["qstick"].fillna(0) <= {variant.vi_spread_min}) & (dataframe["qstick_slope"].fillna(0) >= {variant.vi_slope_min}) & (dataframe["close"] > dataframe["ema21"])'
        if is_reversal
        else f'(dataframe["qstick"].fillna(0) >= {variant.vi_spread_min}) & (dataframe["qstick_slope"].fillna(0) >= {variant.vi_slope_min})'
    )
    return f'''from freqtrade.strategy import IStrategy
from pandas import DataFrame


class {name}(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "{timeframe}"
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
        open_ = dataframe["open"]
        volume = dataframe["volume"]
        prev_close = close.shift()
        tr = DataFrame({{"hl": high - low, "hc": (high - prev_close).abs(), "lc": (low - prev_close).abs()}}).max(axis=1)
        dataframe["atr"] = tr.rolling(14).mean()
        body = (close - open_) / dataframe["atr"].replace(0, 1)
        dataframe["qstick"] = body.rolling({variant.vi_period}).mean()
        dataframe["qstick_slope"] = dataframe["qstick"] - dataframe["qstick"].shift(5)
        dataframe["body_abs_atr"] = body.abs()
        dataframe["ema21"] = close.ewm(span=21, adjust=False).mean()
        dataframe["ema55"] = close.ewm(span=55, adjust=False).mean()
        dataframe["ema144"] = close.ewm(span=144, adjust=False).mean()
        dataframe["ema_slope_atr"] = (dataframe["ema21"] - dataframe["ema21"].shift(12)) / dataframe["atr"].replace(0, 1)
        dataframe["pullback_atr"] = (close - dataframe["ema21"]).abs() / dataframe["atr"].replace(0, 1)
        dataframe["range_expansion"] = (high - low).abs() / (high - low).abs().rolling(60).mean().replace(0, 1)
        dataframe["rvol"] = volume / volume.rolling(60).mean().replace(0, 1)
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean().replace(0, 1e-9)
        dataframe["rsi14"] = 100.0 - (100.0 / (1.0 + gain / loss))
        minute = dataframe["date"].dt.hour * 60 + dataframe["date"].dt.minute
        if "{timeframe}" == "1d":
            dataframe["entry_window"] = True
            dataframe["force_exit_window"] = False
        else:
            dataframe["entry_window"] = ((minute >= 13 * 60 + 35) & (minute <= 20 * 60 + 35)) | ((minute >= 0) & (minute <= 2 * 60 + 10))
            dataframe["force_exit_window"] = (minute >= 20 * 60 + 50) & (minute < 21 * 60 + 55)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        qstick_signal = ({qstick_clause})
        signal = (
            dataframe["entry_window"]
            & qstick_signal
            & (dataframe["ema_slope_atr"].fillna(0) >= {variant.ema_slope_min})
            & (dataframe["close"] >= dataframe["ema144"] - dataframe["atr"] * 0.35)
            & (dataframe["pullback_atr"] <= {variant.pullback_atr_max})
            & (dataframe["rvol"] >= {variant.rvol_min})
            & (dataframe["range_expansion"] >= 0.72)
            & dataframe["rsi14"].between(38, 82)
        )
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{tag}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        body_rollover = dataframe["qstick_slope"] < -0.00055
        momentum_lost = (dataframe["close"] < dataframe["ema21"] - dataframe["atr"] * 0.55) | (dataframe["rsi14"] < 37)
        dataframe.loc[dataframe["force_exit_window"] | body_rollover | momentum_lost, "exit_long"] = 1
        return dataframe
'''


def write_materials(data_paths: Path | dict[str, Path]) -> list[Path]:
    if isinstance(data_paths, Path):
        data_paths = {"1m": data_paths}
    materials: list[Path] = []
    for timeframe, data_path in data_paths.items():
        for variant in base.VARIANTS:
            klass = class_name(variant, timeframe)
            strategy = base.ROOT / "agent-material" / f"{klass}.py"
            strategy.write_text(strategy_source(klass, variant, timeframe), encoding="utf-8")
            material = base.ROOT / "agent-material" / f"ibkr_mnq_qstick_body_momentum_{variant.name}_{timeframe}_mtf_v1.material.json"
            payload = {
                "package_id": f"ibkr-mnq-qstick-body-momentum-{variant.name.replace('_', '-')}-{timeframe}-mtf-v1",
                "title": f"IBKR MNQ Qstick candle-body momentum {variant.name} {timeframe} MTF",
                "symbol": "MNQ", "timeframe": timeframe, "timerange": base.timerange(data_path), "direction": "long",
                "data_path": str(data_path), "strategy_source_path": str(strategy), "strategy_class_name": klass,
                "strategy_brief": "Public Qstick candle-body momentum/reversal family on MNQ retained real IBKR futures MTF data; 1m remains the origin and higher frames provide context/resonance evidence.",
                "evaluation_priority": ["public_family_diversity", "candle_body_momentum", "mtf_resonance", "exact_1m_cost_density"],
                "consumer_evidence_profile": {
                    "branch_path": base.BRANCH_PATH, "regime_profit_branch_path": base.BRANCH_PATH, "branch_id": base.FACTOR_ID,
                    "market": "FUTURES", "product": "equity_index", "root_symbol": "MNQ", "root_timeframe": "1m",
                    "main_regime": "CandleBodyMomentum", "sub_regime": "QstickBodyMomentum",
                    "sub_sub_regime_or_profit_factor": "QstickBodyMomentum", "profit_factor": base.FACTOR_ID,
                    "profit_factor_id": base.FACTOR_ID,
                    "base_timeframe": "1m", "training_timeframe": "1m", "material_timeframe": timeframe,
                    "provider": "IBKR", "provider_window": "retained_full_ladder", "provider_provenance": f"IBKR FUT MNQ 202606 {timeframe} retained source={base.SOURCE_ROOT.name}",
                    "source_backed_family": "Qstick candle-body momentum", "asset_class": "futures", "sec_type": "FUT", "exchange": "CME", "multiplier": "2", "last_trade_date": "202606",
                    "gate_id": "Gate1IbkrMnqQstickBodyMomentum1mMtf", "promotion_allowed": False, "trade_usable": False, "update_goal": False,
                },
                "notes": ["public_family=qstick", "local_cache_replay=false_retained_real_ibkr_mtf_ladder", "downstream_forbidden_until_exact_1m_5bps_survives"],
            }
            material.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            materials.append(material)
    return materials


def main() -> int:
    for sub in ["data/provider/normalized", "agent-material", "summaries", "checks", "command-output", "state", "scripts", "materials"]:
        (base.ROOT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(__file__, base.ROOT / "scripts" / Path(__file__).name)
    (base.ROOT / "materials/source_manifest.json").write_text(json.dumps([
        {"source": "public Qstick candle-body momentum indicator family", "use": "diversity Gate 1 idea after dense negative EOM/KVO samples"},
        {"source": "retained IBKR MNQ 202606 full MTF provider packet", "timeframes": {tf: str(path) for tf, path in TIMEFRAME_SOURCES.items()}},
    ], indent=2) + "\n", encoding="utf-8")
    missing = [str(path) for path in TIMEFRAME_SOURCES.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(missing)
    data_paths = {}
    provider_rows = []
    for timeframe, source in TIMEFRAME_SOURCES.items():
        data_path = base.ROOT / "data/provider/normalized" / source.name
        shutil.copy2(source, data_path)
        data_paths[timeframe] = data_path
        provider_rows.append({"provider": "IBKR", "sec_type": "FUT", "symbol": "MNQ", "product": "equity_index", "exchange": "CME", "last_trade_date": "202606", "timeframe": timeframe, "duration": "retained", "rows": base.row_count(data_path), "path": str(data_path), "source_provider_root": str(base.SOURCE_ROOT), "local_cache_replay": "false_retained_real_ibkr_mtf_ladder"})
    with (base.ROOT / "summaries/provider_provenance_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(provider_rows[0].keys())); writer.writeheader(); writer.writerows(provider_rows)
    materials = write_materials(data_paths)
    strategies = [Path(json.loads(path.read_text())["strategy_source_path"]) for path in materials]
    commands = [base.run_cmd("00_strategy_py_compile", [base.PY, "-m", "py_compile", *strategies], timeout=120)]
    if commands[-1]["exit"] == 0:
        args: list[object] = [base.ICT, "auto-quant-agent-material-batch", "--symbol", base.AQ_SYMBOL, "--state-dir", base.ROOT / "state", "--max-parallel", "1"]
        if base.AQ_REPO.exists(): args += ["--repo-url", base.AQ_REPO]
        for material in materials: args += ["--material", material]
        commands.append(base.run_cmd("01_auto_quant_agent_material_batch", args, timeout=900))
    if commands[-1]["exit"] == 0:
        commands.append(base.run_cmd("02_auto_quant_agent_material_dispatch", [base.ICT, "auto-quant-agent-material-dispatch", "--symbol", base.AQ_SYMBOL, "--state-dir", base.ROOT / "state"], timeout=1200))
    if commands[-1]["exit"] == 0:
        commands.append(base.run_cmd("03_auto_quant_agent_material_rank", [base.ICT, "auto-quant-agent-material-rank", "--symbol", base.AQ_SYMBOL, "--state-dir", base.ROOT / "state"], timeout=240))
    rank_rows = base.latest_rank_rows() if commands[-1]["name"] == "03_auto_quant_agent_material_rank" and commands[-1]["exit"] == 0 else []
    representative_price = base.cost_model.representative_price_from_provider_rows(provider_rows)
    cost_rows, survivors_instrument_cost, branch_ok = score_rank_rows_with_instrument_cost(
        rank_rows,
        representative_price=representative_price,
    )
    cost_packet = base.cost_model.cost_model_packet("MNQ", representative_price)
    exact_1m_survivors_instrument_cost = [row["label"] for row in cost_rows if row["survives_instrument_cost"] and row["label"].endswith("/1m")]
    ranked_timeframes = sorted({str(row["label"]).rsplit("/", 1)[-1] for row in cost_rows})
    branch_paths = sorted({str(row.get("branch_path") or "") for row in rank_rows})
    downstream = branch_ok and bool(exact_1m_survivors_instrument_cost)
    decision = "gate1_ibkr_mnq1m_qstick_body_momentum_downstream_allowed" if downstream else "drop_or_block_gate1_practical"
    metrics = {"run_root": str(base.ROOT), "source_provider_root": str(base.SOURCE_ROOT), "factor_id": base.FACTOR_ID, "branch_path": base.BRANCH_PATH, "decision": decision, "source_backed_family": "Qstick candle-body momentum", "provider_rows": provider_rows, "material_timeframes": list(TIMEFRAME_SOURCES.keys()), "ranked_timeframes": ranked_timeframes, "rank_rows": len(rank_rows), "rank_total_trade_count": sum(int(row.get("trade_count") or 0) for row in rank_rows), "representative_price": representative_price, "cost_model": cost_packet, "promotion_cost_verified": bool(cost_packet.get("verified_for_promotion")), "mtf_instrument_cost_rows": cost_rows, "exact_1m_survivors_instrument_cost": exact_1m_survivors_instrument_cost, "all_timeframe_survivors_instrument_cost": survivors_instrument_cost, "branch_paths": branch_paths, "branch_fields_preserved": branch_ok, "downstream_allowed": downstream, "pre_bayes_allowed": downstream, "bbn_allowed": downstream, "catboost_allowed": downstream, "execution_tree_allowed": downstream, "promotion_allowed": False, "trade_usable": False, "update_goal": False, "local_cache_replay": False, "command_exits": {cmd["name"]: cmd["exit"] for cmd in commands}, "skill_update": "needed_after_downstream" if downstream else "not_needed"}
    (base.ROOT / "checks/terminal_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    base.cost_model.write_real_fee_rank_rows_csv(base.ROOT / "summaries/rank_rows.csv", cost_rows)
    lines = base.cost_model.real_fee_rank_table_lines(
        decision=decision,
        title="MNQ MTF Qstick body-momentum rows:",
        rows=cost_rows,
        branch_ok=branch_ok,
        survivors=survivors_instrument_cost,
        downstream=downstream,
    )
    lines.insert(4, "Source: public Qstick candle-body momentum family; rewritten as Freqtrade/AQ material.")
    lines.insert(5, "")
    lines += [f"- `ranked_timeframes={ranked_timeframes}`", f"- `exact_1m_survivors_instrument_cost={exact_1m_survivors_instrument_cost}`"]
    (base.ROOT / "summaries/terminal_decision_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0 if commands and commands[-1]["name"] == "03_auto_quant_agent_material_rank" and commands[-1]["exit"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
