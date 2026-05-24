#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
BASE = REPO / "support/docs/experiments/actionable-regime-confidence"
STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
ROOT = BASE / "runs" / f"{STAMP}-codex-ibkr-mgc1m-vortex-trend-continuation-7d-gate1-v1"
SOURCE_ROOT = BASE / "runs/20260519T232924+0800-codex-ibkr-mgc1m-opening-vwap-rvol-reclaim-7d-gate1-v1"
SOURCE_DATA = SOURCE_ROOT / "data/provider/normalized/ibkr_mgc_202606_1m_7d.csv"
PY = Path("/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python")
if not PY.exists():
    PY = Path("python3")
ICT = REPO / ".local-artifacts/cargo-target/debug/ict-engine"
if not ICT.exists():
    ICT = REPO / "target/debug/ict-engine"
AQ_REPO = Path("/Users/thrill3r/Auto-Quant")

AQ_SYMBOL = "IBKR_MGC1M_VORTEX_TREND_CONTINUATION_7D_GATE1_V1"
FACTOR_ID = "ibkr_mgc1m_vortex_trend_continuation_7d_gate1_v1"
BRANCH_PATH = "TrendExpansion -> VortexTrendContinuation -> ibkr_mgc1m_vortex_trend_continuation_7d_gate1_v1"
ROOT_SYMBOL = "MGC"
PRODUCT = "precious_metals"
EXCHANGE = "COMEX"
MULTIPLIER = "10"
CONTRACT_FILE_TOKEN = "mgc"
LAST_TRADE_DATE = "202606"
SOURCE_BACKED_FAMILY = "Vortex Indicator / VI trend continuation"
SUMMARY_TABLE_TITLE = "Exact MGC 1m Vortex/VI trend-continuation rows:"


@dataclass(frozen=True)
class Variant:
    name: str
    vi_period: int
    vi_spread_min: float
    vi_slope_min: float
    rvol_min: float
    ema_slope_min: float
    pullback_atr_max: float
    roi: float
    stoploss: float
    trail: float
    offset: float


VARIANTS = [
    Variant("vi_dense", 14, 0.015, -0.004, 0.45, -0.030, 0.95, 0.0022, -0.0060, 0.0008, 0.0022),
    Variant("vi_balanced", 18, 0.030, 0.000, 0.58, -0.010, 0.75, 0.0030, -0.0070, 0.0010, 0.0030),
    Variant("vi_quality", 22, 0.050, 0.003, 0.72, 0.015, 0.60, 0.0040, -0.0082, 0.0013, 0.0040),
    Variant("vi_reclaim", 14, 0.005, 0.004, 0.52, -0.020, 0.80, 0.0026, -0.0065, 0.0009, 0.0026),
]


def run_cmd(name: str, argv: list[object], timeout: int = 300) -> dict:
    (ROOT / "command-output").mkdir(parents=True, exist_ok=True)
    (ROOT / "checks").mkdir(parents=True, exist_ok=True)
    argv_s = [str(item) for item in argv]
    (ROOT / "command-output" / f"{name}.cmd").write_text(" ".join(argv_s) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(argv_s, cwd=REPO, text=True, capture_output=True, timeout=timeout)
        stdout, stderr, rc, timed_out = proc.stdout, proc.stderr, proc.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n"
        rc, timed_out = 124, True
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    (ROOT / "command-output" / f"{name}.out").write_text(stdout, encoding="utf-8")
    (ROOT / "command-output" / f"{name}.err").write_text(stderr, encoding="utf-8")
    (ROOT / "checks" / f"{name}.exit").write_text(f"{rc}\n", encoding="utf-8")
    return {"name": name, "exit": rc, "timed_out": timed_out}


def timerange(path: Path) -> str:
    dates: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw = (row.get("timestamp") or "").strip()
            if raw:
                dates.append(raw[:10].replace("-", ""))
    return f"{min(dates)}-{max(dates)}" if dates else ""


def row_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def class_name(variant: Variant) -> str:
    safe = "".join(part.title() for part in variant.name.split("_"))
    return f"IbkrMgcVortexTrendContinuation{safe}1MinV1"


def strategy_source(name: str, variant: Variant) -> str:
    tag = f"{FACTOR_ID}_{variant.name}"
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
        dataframe["ema_slope_atr"] = (dataframe["ema21"] - dataframe["ema21"].shift(12)) / dataframe["atr"].replace(0, 1)
        dataframe["rvol"] = dataframe["volume"] / dataframe["volume"].rolling(60).mean().replace(0, 1)

        vm_plus = (high - low.shift()).abs()
        vm_minus = (low - high.shift()).abs()
        tr_sum = tr.rolling({variant.vi_period}).sum().replace(0, 1e-9)
        dataframe["vi_plus"] = vm_plus.rolling({variant.vi_period}).sum() / tr_sum
        dataframe["vi_minus"] = vm_minus.rolling({variant.vi_period}).sum() / tr_sum
        dataframe["vi_spread"] = dataframe["vi_plus"] - dataframe["vi_minus"]
        dataframe["vi_slope"] = dataframe["vi_spread"] - dataframe["vi_spread"].shift(5)
        dataframe["pullback_atr"] = (close - dataframe["ema21"]).abs() / dataframe["atr"].replace(0, 1)
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
            & (dataframe["vi_plus"] > dataframe["vi_minus"])
            & (dataframe["vi_spread"] >= {variant.vi_spread_min})
            & (dataframe["vi_slope"].fillna(0) >= {variant.vi_slope_min})
            & (dataframe["ema_slope_atr"].fillna(0) >= {variant.ema_slope_min})
            & (dataframe["close"] >= dataframe["ema144"] - dataframe["atr"] * 0.25)
            & (dataframe["pullback_atr"] <= {variant.pullback_atr_max})
            & (dataframe["rvol"] >= {variant.rvol_min})
            & dataframe["rsi14"].between(42, 78)
        )
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{tag}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        vortex_flip = dataframe["vi_plus"] < dataframe["vi_minus"]
        momentum_lost = (dataframe["vi_spread"] < 0) | (dataframe["close"] < dataframe["ema21"] - dataframe["atr"] * 0.45)
        dataframe.loc[dataframe["force_exit_window"] | vortex_flip | momentum_lost, "exit_long"] = 1
        return dataframe
'''


def latest_rank_rows() -> list[dict]:
    files = sorted((ROOT / f"state/auto-quant/{AQ_SYMBOL}").glob("auto_quant_agent_material_rank.*.json"))
    if not files:
        return []
    return json.loads(files[-1].read_text(encoding="utf-8")).get("ranking", []) or []


def safe_float(value: object) -> float:
    try:
        return float(str(value))
    except Exception:
        return 0.0


def cost_survives(trade_count: int, cost_stressed_total_profit_pct: float) -> bool:
    return trade_count > 0 and cost_stressed_total_profit_pct > 0


def hard_gate_downstream_allowed(branch_fields_preserved: bool, exact_1m_5bps: list[str]) -> bool:
    return bool(branch_fields_preserved and exact_1m_5bps)


def label_for(row: dict) -> str:
    package = str(row.get("package_id") or "")
    variant = next((item.name for item in VARIANTS if item.name.replace("_", "-") in package), "unknown")
    return f"MGC/{variant}/1m"


def write_materials(data_path: Path) -> list[Path]:
    materials: list[Path] = []
    for variant in VARIANTS:
        klass = class_name(variant)
        strategy = ROOT / "agent-material" / f"{klass}.py"
        strategy.write_text(strategy_source(klass, variant), encoding="utf-8")
        material = ROOT / "agent-material" / f"ibkr_mgc_vortex_trend_continuation_{variant.name}_1m_7d_v1.material.json"
        payload = {
            "package_id": f"ibkr-mgc-vortex-trend-continuation-{variant.name.replace('_', '-')}-1m-7d-v1",
            "title": f"IBKR MGC Vortex trend continuation {variant.name} 1m 7D",
            "symbol": "MGC",
            "timeframe": "1m",
            "timerange": timerange(data_path),
            "direction": "long",
            "data_path": str(data_path),
            "strategy_source_path": str(strategy),
            "strategy_class_name": klass,
            "strategy_brief": "Classic Vortex Indicator / VI trend-continuation family on MGC 1m real IBKR futures data; diversity lane distinct from VWAP, RSI, RVOL, liquidity sweep, pivots, PSAR, Donchian, Keltner, ADX, SuperTrend, and market-profile families.",
            "evaluation_priority": ["public_family_diversity", "exact_1m_cost_density", "precious_metals_provider_parity"],
            "consumer_evidence_profile": {
                "branch_path": BRANCH_PATH,
                "regime_profit_branch_path": BRANCH_PATH,
                "branch_id": FACTOR_ID,
                "market": "FUTURES",
                "product": "precious_metals",
                "root_symbol": "MGC",
                "root_timeframe": "1m",
                "main_regime": "TrendExpansion",
                "sub_regime": "VortexTrendContinuation",
                "sub_sub_regime_or_profit_factor": FACTOR_ID,
                "profit_factor": FACTOR_ID,
                "base_timeframe": "1m",
                "training_timeframe": "1m",
                "material_timeframe": "1m",
                "provider": "IBKR",
                "provider_window": "7 D",
                "provider_provenance": f"IBKR FUT MGC 202606 1m 7 D source={SOURCE_ROOT.name}",
                "source_backed_family": "Vortex Indicator / VI trend continuation",
                "asset_class": "futures",
                "sec_type": "FUT",
                "exchange": "COMEX",
                "multiplier": "10",
                "last_trade_date": "202606",
                "gate_id": "Gate1IbkrMgcVortexTrendContinuation1m7d",
                "promotion_allowed": False,
                "trade_usable": False,
                "update_goal": False,
            },
            "notes": ["public_family=vortex_indicator", "local_cache_replay=false_source_provider_root_reused", "downstream_forbidden_until_cost_density_survives"],
        }
        material.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        materials.append(material)
    return materials


def main() -> int:
    for sub in ["data/provider/normalized", "agent-material", "summaries", "checks", "command-output", "state", "scripts"]:
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(__file__, ROOT / "scripts" / Path(__file__).name)
    if not SOURCE_DATA.exists():
        raise FileNotFoundError(SOURCE_DATA)
    data_path = ROOT / f"data/provider/normalized/ibkr_{CONTRACT_FILE_TOKEN}_{LAST_TRADE_DATE}_1m_7d.csv"
    shutil.copy2(SOURCE_DATA, data_path)
    provider_rows = [{
        "provider": "IBKR", "sec_type": "FUT", "symbol": ROOT_SYMBOL, "product": PRODUCT,
        "exchange": EXCHANGE, "last_trade_date": LAST_TRADE_DATE, "timeframe": "1m", "duration": "7 D",
        "rows": row_count(data_path), "path": str(data_path), "source_provider_root": str(SOURCE_ROOT),
        "local_cache_replay": "false_source_provider_root_reused",
    }]
    with (ROOT / "summaries/provider_provenance_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(provider_rows[0].keys()))
        writer.writeheader(); writer.writerows(provider_rows)
    materials = write_materials(data_path)
    strategies = [Path(json.loads(path.read_text())["strategy_source_path"]) for path in materials]
    commands = [run_cmd("00_strategy_py_compile", [PY, "-m", "py_compile", *strategies], timeout=120)]
    if commands[-1]["exit"] == 0:
        args: list[object] = [ICT, "auto-quant-agent-material-batch", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state", "--max-parallel", "1"]
        if AQ_REPO.exists():
            args += ["--repo-url", AQ_REPO]
        for material in materials:
            args += ["--material", material]
        commands.append(run_cmd("01_auto_quant_agent_material_batch", args, timeout=900))
    if commands[-1]["exit"] == 0:
        commands.append(run_cmd("02_auto_quant_agent_material_dispatch", [ICT, "auto-quant-agent-material-dispatch", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"], timeout=1200))
    if commands[-1]["exit"] == 0:
        commands.append(run_cmd("03_auto_quant_agent_material_rank", [ICT, "auto-quant-agent-material-rank", "--symbol", AQ_SYMBOL, "--state-dir", ROOT / "state"], timeout=240))

    rank_rows = latest_rank_rows() if commands[-1]["name"] == "03_auto_quant_agent_material_rank" and commands[-1]["exit"] == 0 else []
    cost_rows = []
    for row in rank_rows:
        trades = int(row.get("trade_count") or 0)
        gross = safe_float(row.get("total_profit_pct"))
        record = {"label": label_for(row), "status": row.get("status"), "trade_count": trades, "win_rate_pct": safe_float(row.get("win_rate_pct")), "raw_total_profit_pct": gross, "sharpe": safe_float(row.get("sharpe")), "branch_path": row.get("branch_path")}
        for bps in (0, 1, 2, 5):
            record[f"{bps}bps_per_side_total_profit_pct"] = round(gross - trades * bps * 0.02, 6)
        record["survives_2bps_per_side"] = cost_survives(trades, record["2bps_per_side_total_profit_pct"])
        record["survives_5bps_per_side"] = cost_survives(trades, record["5bps_per_side_total_profit_pct"])
        cost_rows.append(record)
    survivors_2 = [row["label"] for row in cost_rows if row["survives_2bps_per_side"]]
    survivors_5 = [row["label"] for row in cost_rows if row["survives_5bps_per_side"]]
    branch_paths = sorted({str(row.get("branch_path") or "") for row in rank_rows})
    branch_ok = bool(rank_rows) and branch_paths == [BRANCH_PATH]
    downstream = hard_gate_downstream_allowed(branch_ok, survivors_5)
    decision = globals().get("DOWNSTREAM_DECISION", "gate1_ibkr_mgc1m_vortex_trend_continuation_downstream_allowed") if downstream else globals().get("BLOCKED_DECISION", "drop_or_block_gate1_practical")
    metrics = {
        "run_root": str(ROOT), "source_provider_root": str(SOURCE_ROOT), "factor_id": FACTOR_ID, "branch_path": BRANCH_PATH,
        "decision": decision, "source_backed_family": SOURCE_BACKED_FAMILY, "provider_rows": provider_rows, "rank_rows": len(rank_rows),
        "rank_total_trade_count": sum(int(row.get("trade_count") or 0) for row in rank_rows),
        "exact_1m_cost_stress": cost_rows, "exact_1m_survivors_2bps": survivors_2,
        "exact_1m_survivors_5bps": survivors_5, "branch_paths": branch_paths,
        "branch_fields_preserved": branch_ok, "downstream_allowed": downstream,
        "pre_bayes_allowed": downstream, "bbn_allowed": downstream, "catboost_allowed": downstream,
        "execution_tree_allowed": downstream, "promotion_allowed": False, "trade_usable": False,
        "update_goal": False, "local_cache_replay": False,
        "command_exits": {cmd["name"]: cmd["exit"] for cmd in commands},
        "skill_update": "needed_after_downstream" if downstream else "not_needed",
    }
    (ROOT / "checks/terminal_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    with (ROOT / "summaries/rank_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["label", "status", "trade_count", "win_rate_pct", "raw_total_profit_pct", "1bps_per_side_total_profit_pct", "2bps_per_side_total_profit_pct", "5bps_per_side_total_profit_pct", "survives_2bps_per_side", "survives_5bps_per_side", "branch_path"]
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows([{key: row.get(key, "") for key in fields} for row in cost_rows])
    lines = ["# Terminal Decision Summary", "", f"Decision: `{decision}`", "", SUMMARY_TABLE_TITLE, "", "| label | trades | win_rate | raw | 1bps | 2bps | 5bps |", "|---|---:|---:|---:|---:|---:|---:|"]
    for row in cost_rows:
        lines.append(f"| `{row['label']}` | {row['trade_count']} | {row['win_rate_pct']:.4f}% | {row['raw_total_profit_pct']:.2f}% | {row['1bps_per_side_total_profit_pct']:.2f}% | {row['2bps_per_side_total_profit_pct']:.2f}% | {row['5bps_per_side_total_profit_pct']:.2f}% |")
    lines += ["", f"- `branch_fields_preserved={branch_ok}`", f"- `exact_1m_survivors_2bps={survivors_2}`", f"- `exact_1m_survivors_5bps={survivors_5}`", f"- `downstream_allowed={downstream}`", ""]
    (ROOT / "summaries/terminal_decision_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0 if commands and commands[-1]["name"] == "03_auto_quant_agent_material_rank" and commands[-1]["exit"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
