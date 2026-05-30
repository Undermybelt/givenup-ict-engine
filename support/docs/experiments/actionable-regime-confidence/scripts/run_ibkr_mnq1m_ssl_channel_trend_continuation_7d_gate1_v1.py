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
BASE_SCRIPT = SCRIPT.with_name("run_ibkr_mgc1m_vortex_trend_continuation_7d_gate1_v1.py")
spec = importlib.util.spec_from_file_location("ibkr_gate1_template", BASE_SCRIPT)
base = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = base
spec.loader.exec_module(base)

STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
base.ROOT = base.BASE / "runs" / f"{STAMP}-codex-ibkr-mnq1m-ssl-channel-trend-continuation-7d-gate1-v1"
base.SOURCE_ROOT = base.BASE / "runs/20260520T021030+0800-codex-ibkr-mnq1m-gap-fade-go-7d-gate1-v1"
base.SOURCE_DATA = base.SOURCE_ROOT / "data/provider/normalized/ibkr_mnq_202606_1m_7d.csv"
base.AQ_SYMBOL = "IBKR_MNQ1M_SSL_CHANNEL_TREND_CONTINUATION_7D_GATE1_V1"
base.FACTOR_ID = "ibkr_mnq1m_ssl_channel_trend_continuation_7d_gate1_v1"
base.BRANCH_PATH = "TrendExpansion -> SslChannelTrendContinuation -> SslChannelTrendContinuation -> ibkr_mnq1m_ssl_channel_trend_continuation_7d_gate1_v1"


@dataclass(frozen=True)
class Variant:
    name: str
    ssl_period: int
    atr_mult: float
    slope_lookback: int
    slope_min: float
    channel_buffer_atr: float
    pullback_atr_max: float
    rvol_floor: float
    min_hold_bars: int
    roi: float
    stoploss: float
    trail: float
    offset: float


VARIANTS = [
    Variant("ssl_dense", 10, 0.55, 9, -0.035, -0.18, 0.92, 0.25, 4, 0.0028, -0.0068, 0.0009, 0.0028),
    Variant("ssl_balanced", 14, 0.70, 12, -0.010, -0.08, 0.74, 0.35, 5, 0.0038, -0.0080, 0.0012, 0.0038),
    Variant("ssl_quality", 18, 0.85, 16, 0.020, 0.02, 0.58, 0.48, 6, 0.0052, -0.0094, 0.0017, 0.0052),
    Variant("ssl_retest", 12, 0.62, 10, -0.020, -0.14, 0.82, 0.30, 4, 0.0032, -0.0074, 0.0010, 0.0032),
]


def class_name(variant: Variant) -> str:
    safe = "".join(part.title() for part in variant.name.split("_"))
    return f"IbkrMnqSslChannelTrendContinuation{safe}1MinV1"


def label_for(row: dict) -> str:
    package = str(row.get("package_id") or "")
    variant = next((item.name for item in VARIANTS if item.name.replace("_", "-") in package), "unknown")
    return f"MNQ/{variant}/1m"


def build_cost_summary(
    rank_rows: list[dict],
    *,
    representative_price: float,
) -> tuple[list[dict], list[str], list[str], bool, bool]:
    summary = base.cost_model.rank_rows_real_fee_summary(
        rank_rows,
        symbol="MNQ",
        representative_price=representative_price,
        label_fn=label_for,
    )
    cost_rows = list(summary["rows"])
    survivors_instrument_cost = list(summary["survivors"])
    branch_paths = sorted({str(row.get("branch_path") or "") for row in rank_rows})
    branch_ok = bool(rank_rows) and branch_paths == [base.BRANCH_PATH]
    downstream = branch_ok and bool(survivors_instrument_cost)
    return cost_rows, survivors_instrument_cost, branch_paths, branch_ok, downstream


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
    startup_candle_count = 260

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        high = dataframe["high"]
        low = dataframe["low"]
        close = dataframe["close"]
        prev_close = close.shift()
        tr = DataFrame({{"hl": high - low, "hc": (high - prev_close).abs(), "lc": (low - prev_close).abs()}}).max(axis=1)
        dataframe["atr"] = tr.rolling(14).mean()
        sma_high = high.rolling({variant.ssl_period}).mean()
        sma_low = low.rolling({variant.ssl_period}).mean()
        dataframe["ssl_up"] = sma_high + dataframe["atr"] * {variant.atr_mult}
        dataframe["ssl_down"] = sma_low - dataframe["atr"] * {variant.atr_mult}
        dataframe["ssl_mid"] = (dataframe["ssl_up"] + dataframe["ssl_down"]) / 2.0
        dataframe["ssl_slope_atr"] = (dataframe["ssl_mid"] - dataframe["ssl_mid"].shift({variant.slope_lookback})) / dataframe["atr"].replace(0, 1)
        dataframe["ema55"] = close.ewm(span=55, adjust=False).mean()
        dataframe["ema144"] = close.ewm(span=144, adjust=False).mean()
        dataframe["ema_slope_atr"] = (dataframe["ema55"] - dataframe["ema55"].shift(12)) / dataframe["atr"].replace(0, 1)
        dataframe["channel_position"] = (close - dataframe["ssl_mid"]) / dataframe["atr"].replace(0, 1)
        dataframe["pullback_atr"] = (close - dataframe["ssl_mid"]).abs() / dataframe["atr"].replace(0, 1)
        dataframe["breakout_bar"] = (close > dataframe["ssl_up"]) & (close.shift(1) <= dataframe["ssl_up"].shift(1))
        dataframe["ssl_reclaim"] = (close > dataframe["ssl_mid"]) & (close.shift(1) <= dataframe["ssl_mid"].shift(1))
        dataframe["rvol"] = dataframe["volume"] / dataframe["volume"].rolling(60).mean().replace(0, 1)
        minute = dataframe["date"].dt.hour * 60 + dataframe["date"].dt.minute
        dataframe["entry_window"] = ((minute >= 13 * 60 + 35) & (minute <= 20 * 60 + 35)) | ((minute >= 0) & (minute <= 2 * 60 + 10))
        dataframe["force_exit_window"] = (minute >= 20 * 60 + 50) & (minute < 21 * 60 + 55)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        continuation = dataframe["breakout_bar"] | dataframe["ssl_reclaim"] | (dataframe["channel_position"] >= {variant.channel_buffer_atr})
        signal = (
            dataframe["entry_window"]
            & continuation.fillna(False)
            & (dataframe["ssl_slope_atr"].fillna(0) >= {variant.slope_min})
            & (dataframe["ema_slope_atr"].fillna(0) >= {variant.slope_min} * 0.5)
            & (dataframe["close"] >= dataframe["ema144"] - dataframe["atr"] * 0.35)
            & (dataframe["pullback_atr"] <= {variant.pullback_atr_max})
            & (dataframe["rvol"] >= {variant.rvol_floor})
        )
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{tag}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        channel_fail = dataframe["close"] < dataframe["ssl_mid"] - dataframe["atr"] * 0.45
        slope_fail = dataframe["ssl_slope_atr"] < -0.10
        dataframe.loc[dataframe["force_exit_window"] | channel_fail | slope_fail, "exit_long"] = 1
        return dataframe
'''


def write_materials(data_path: Path) -> list[Path]:
    materials: list[Path] = []
    for variant in VARIANTS:
        klass = class_name(variant)
        strategy = base.ROOT / "agent-material" / f"{klass}.py"
        strategy.write_text(strategy_source(klass, variant), encoding="utf-8")
        material = base.ROOT / "agent-material" / f"ibkr_mnq_ssl_channel_trend_continuation_{variant.name}_1m_7d_v1.material.json"
        payload = {
            "package_id": f"ibkr-mnq-ssl-channel-trend-continuation-{variant.name.replace('_', '-')}-1m-7d-v1",
            "title": f"IBKR MNQ SSL channel trend continuation {variant.name} 1m 7D",
            "symbol": "MNQ",
            "timeframe": "1m",
            "timerange": base.timerange(data_path),
            "direction": "long",
            "data_path": str(data_path),
            "strategy_source_path": str(strategy),
            "strategy_class_name": klass,
            "strategy_brief": "Public SSL Channel / moving-average channel trend-continuation family on retained real IBKR MNQ 1m futures data; branch deliberately distinct from VWAP/RSI/RVOL, liquidity-sweep, Bollinger, SuperTrend, Keltner, Donchian, and oscillator-reclaim lanes.",
            "evaluation_priority": ["public_family_diversity", "ssl_channel_continuation", "exact_1m_cost_density"],
            "consumer_evidence_profile": {
                "branch_path": base.BRANCH_PATH,
                "regime_profit_branch_path": base.BRANCH_PATH,
                "branch_id": base.FACTOR_ID,
                "market": "FUTURES",
                "product": "equity_index",
                "root_symbol": "MNQ",
                "root_timeframe": "1m",
                "main_regime": "TrendExpansion",
                "sub_regime": "SslChannelTrendContinuation",
                "sub_sub_regime_or_profit_factor": "SslChannelTrendContinuation",
                "profit_factor_id": base.FACTOR_ID,
                "profit_factor": base.FACTOR_ID,
                "base_timeframe": "1m",
                "training_timeframe": "1m",
                "material_timeframe": "1m",
                "provider": "IBKR",
                "provider_window": "7 D",
                "provider_provenance": f"IBKR FUT MNQ 202606 1m 7 D retained source={base.SOURCE_ROOT.name}",
                "source_backed_family": "SSL Channel / moving-average channel trend continuation",
                "asset_class": "futures",
                "sec_type": "FUT",
                "exchange": "CME",
                "multiplier": "2",
                "last_trade_date": "202606",
                "gate_id": "Gate1IbkrMnqSslChannelTrendContinuation1m7d",
                "promotion_allowed": False,
                "trade_usable": False,
                "update_goal": False,
            },
            "notes": ["public_family=ssl_channel_trend_continuation", "local_cache_replay=false_retained_real_ibkr_same_session", "downstream_forbidden_until_cost_density_survives"],
        }
        material.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        materials.append(material)
    return materials


def main() -> int:
    for sub in ["data/provider/normalized", "agent-material", "summaries", "checks", "command-output", "state", "scripts", "materials"]:
        (base.ROOT / sub).mkdir(parents=True, exist_ok=True)
    claim = Path(f"/tmp/ict-engine-agent-claims/board-b-factor-refinement/{STAMP}-codex-ibkr-mnq1m-ssl-channel-trend-continuation-7d-gate1-v1.claim")
    claim.parent.mkdir(parents=True, exist_ok=True)
    claim.write_text(
        f"scope=IBKR MNQ/1m SSL Channel trend-continuation Gate 1 public-family diversity lane\n"
        f"branch_path={base.BRANCH_PATH}\n"
        f"script={SCRIPT}\n"
        f"run_root={base.ROOT}\n"
        "non_takeover=targeted scan found no exact SSL Channel terminal row, claim, or script; avoids active M2K/MNQ/SI downstream and covered VWAP/RSI/RVOL/Bollinger/SuperTrend/Keltner/Donchian/oscillator lanes\n",
        encoding="utf-8",
    )
    shutil.copy2(__file__, base.ROOT / "scripts" / Path(__file__).name)
    (base.ROOT / "materials/source_manifest.json").write_text(json.dumps([
        {"source": "public SSL Channel / MA channel trend-continuation family", "use": "time-tested trend filter and continuation idea; rewritten as AQ/Freqtrade material"},
        {"source": "retained IBKR MNQ 202606 1m 7 D provider packet", "path": str(base.SOURCE_DATA)},
    ], indent=2) + "\n", encoding="utf-8")
    if not base.SOURCE_DATA.exists():
        raise FileNotFoundError(base.SOURCE_DATA)
    data_path = base.ROOT / "data/provider/normalized/ibkr_mnq_202606_1m_7d.csv"
    shutil.copy2(base.SOURCE_DATA, data_path)
    provider_rows = [{"provider": "IBKR", "sec_type": "FUT", "symbol": "MNQ", "product": "equity_index", "exchange": "CME", "last_trade_date": "202606", "timeframe": "1m", "duration": "7 D", "rows": base.row_count(data_path), "path": str(data_path), "source_provider_root": str(base.SOURCE_ROOT), "local_cache_replay": "false_retained_real_ibkr_same_session"}]
    with (base.ROOT / "summaries/provider_provenance_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(provider_rows[0].keys()))
        writer.writeheader()
        writer.writerows(provider_rows)
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
    cost_rows, survivors_instrument_cost, branch_paths, branch_ok, downstream = build_cost_summary(
        rank_rows,
        representative_price=representative_price,
    )
    cost_packet = base.cost_model.cost_model_packet("MNQ", representative_price)
    decision = "gate1_ibkr_mnq1m_ssl_channel_trend_continuation_downstream_allowed" if downstream else "drop_or_block_gate1_practical"
    metrics = {"run_root": str(base.ROOT), "source_provider_root": str(base.SOURCE_ROOT), "factor_id": base.FACTOR_ID, "branch_path": base.BRANCH_PATH, "decision": decision, "source_backed_family": "SSL Channel / moving-average channel trend continuation", "provider_rows": provider_rows, "rank_rows": len(rank_rows), "rank_total_trade_count": sum(int(row.get("trade_count") or 0) for row in rank_rows), "representative_price": representative_price, "cost_model": cost_packet, "promotion_cost_verified": bool(cost_packet.get("verified_for_promotion")), "exact_1m_instrument_cost_rows": cost_rows, "exact_1m_survivors_instrument_cost": survivors_instrument_cost, "branch_paths": branch_paths, "branch_fields_preserved": branch_ok, "downstream_allowed": downstream, "pre_bayes_allowed": downstream, "bbn_allowed": downstream, "catboost_allowed": downstream, "execution_tree_allowed": downstream, "promotion_allowed": False, "trade_usable": False, "update_goal": False, "local_cache_replay": False, "command_exits": {cmd["name"]: cmd["exit"] for cmd in commands}, "skill_update": "needed_after_downstream" if downstream else "not_needed"}
    (base.ROOT / "checks/terminal_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    base.cost_model.write_real_fee_rank_rows_csv(base.ROOT / "summaries/rank_rows.csv", cost_rows)
    lines = base.cost_model.real_fee_rank_table_lines(
        decision=decision,
        title="Exact MNQ 1m SSL-channel trend-continuation rows:",
        rows=cost_rows,
        branch_ok=branch_ok,
        survivors=survivors_instrument_cost,
        downstream=downstream,
    )
    lines.insert(4, "Source: public SSL Channel / moving-average channel trend-continuation family; rewritten as Freqtrade/AQ material.")
    lines.insert(5, "")
    lines += ["Promotion allowed: `false`.", "Trade usable: `false`."]
    (base.ROOT / "summaries/terminal_decision_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (claim).write_text(claim.read_text(encoding="utf-8") + f"terminal_decision={decision}\nterminal_metrics={base.ROOT / 'checks/terminal_metrics.json'}\nterminal_summary={base.ROOT / 'summaries/terminal_decision_summary.md'}\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0 if all(cmd["exit"] == 0 for cmd in commands) else 1


if __name__ == "__main__":
    raise SystemExit(main())
