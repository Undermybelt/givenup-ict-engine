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
ROOT = BASE / "runs" / f"{STAMP}-codex-ibkr-mgc1m-donchian-turtle-breakout-7d-gate1-v1"
SOURCE_ROOT = BASE / "runs/20260519T232924+0800-codex-ibkr-mgc1m-opening-vwap-rvol-reclaim-7d-gate1-v1"
SOURCE_DATA = SOURCE_ROOT / "data/provider/normalized/ibkr_mgc_202606_1m_7d.csv"
PY = Path("/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python")
if not PY.exists():
    PY = Path("python3")
ICT = REPO / ".local-artifacts/cargo-target/debug/ict-engine"
if not ICT.exists():
    ICT = REPO / "target/debug/ict-engine"
AQ_REPO = Path("/Users/thrill3r/Auto-Quant")

AQ_SYMBOL = "IBKR_MGC1M_DONCHIAN_TURTLE_BREAKOUT_7D_GATE1_V1"
FACTOR_ID = "ibkr_mgc1m_donchian_turtle_breakout_7d_gate1_v1"
BRANCH_PATH = "TrendExpansion -> DonchianTurtleBreakout -> ibkr_mgc1m_donchian_turtle_breakout_7d_gate1_v1"


def cost_survives(trade_count: int, cost_stressed_total_profit_pct: float) -> bool:
    return trade_count > 0 and cost_stressed_total_profit_pct > 0


def hard_gate_downstream_allowed(branch_fields_preserved: bool, exact_1m_5bps: list[str]) -> bool:
    return bool(branch_fields_preserved and exact_1m_5bps)


@dataclass(frozen=True)
class Variant:
    name: str
    lookback: int
    exit_lookback: int
    rvol_min: float
    atr_min: float
    atr_max: float
    roi: float
    stoploss: float
    trail: float
    offset: float
    require_compression: bool


VARIANTS = [
    Variant("turtle20_dense", 20, 10, 0.65, 0.00025, 0.0100, 0.0035, -0.0080, 0.0012, 0.0032, False),
    Variant("turtle55_balanced", 55, 20, 0.80, 0.00030, 0.0120, 0.0055, -0.0120, 0.0018, 0.0050, False),
    Variant("compression20", 20, 10, 0.55, 0.00020, 0.0090, 0.0040, -0.0090, 0.0014, 0.0038, True),
    Variant("atr_channel40", 40, 15, 0.70, 0.00025, 0.0110, 0.0048, -0.0100, 0.0016, 0.0045, False),
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
    return f"IbkrMgcDonchianTurtleBreakout{safe}1MinV1"


def strategy_source(name: str, variant: Variant) -> str:
    tag = f"{FACTOR_ID}_{variant.name}"
    compression = "& (dataframe['channel_pct'] <= dataframe['channel_pct_q40'])" if variant.require_compression else ""
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
        dataframe["ema20"] = dataframe["close"].ewm(span=20, adjust=False).mean()
        dataframe["ema50"] = dataframe["close"].ewm(span=50, adjust=False).mean()
        dataframe["ema200"] = dataframe["close"].ewm(span=200, adjust=False).mean()
        tr = DataFrame({{"hl": dataframe["high"] - dataframe["low"], "hc": (dataframe["high"] - dataframe["close"].shift()).abs(), "lc": (dataframe["low"] - dataframe["close"].shift()).abs()}}).max(axis=1)
        dataframe["atr14"] = tr.rolling(14).mean()
        dataframe["atr_pct"] = dataframe["atr14"] / dataframe["close"]
        dataframe["prior_high"] = dataframe["high"].shift(1).rolling({variant.lookback}).max()
        dataframe["exit_low"] = dataframe["low"].shift(1).rolling({variant.exit_lookback}).min()
        dataframe["channel_pct"] = (dataframe["prior_high"] - dataframe["exit_low"]) / dataframe["close"]
        dataframe["channel_pct_q40"] = dataframe["channel_pct"].rolling(220).quantile(0.40)
        dataframe["vol60"] = dataframe["volume"].rolling(60).mean()
        dataframe["rvol"] = dataframe["volume"] / dataframe["vol60"].replace(0, 1)
        dataframe["ema20_slope_atr"] = (dataframe["ema20"] - dataframe["ema20"].shift(12)) / dataframe["atr14"].replace(0, 1)
        minute = dataframe["date"].dt.hour * 60 + dataframe["date"].dt.minute
        dataframe["entry_window"] = ((minute >= 0) & (minute <= 2 * 60 + 30)) | ((minute >= 13 * 60 + 30) & (minute <= 20 * 60 + 30))
        dataframe["force_exit_window"] = (minute >= 20 * 60 + 50) & (minute < 21 * 60 + 55)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        trend_ok = (dataframe["ema20"] > dataframe["ema50"]) & (dataframe["close"] > dataframe["ema20"])
        signal = (
            dataframe["entry_window"]
            & (dataframe["close"] > dataframe["prior_high"])
            & dataframe["atr_pct"].between({variant.atr_min}, {variant.atr_max})
            & (dataframe["rvol"] >= {variant.rvol_min})
            & (dataframe["ema20_slope_atr"].fillna(0) >= -0.01)
            & trend_ok
            {compression}
        )
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "{tag}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        fail = (dataframe["close"] < dataframe["exit_low"]) | (dataframe["close"] < dataframe["ema20"] - dataframe["atr14"] * 0.50)
        dataframe.loc[dataframe["force_exit_window"] | fail, "exit_long"] = 1
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
        material = ROOT / "agent-material" / f"ibkr_mgc_donchian_turtle_breakout_{variant.name}_1m_7d_v1.material.json"
        payload = {
            "package_id": f"ibkr-mgc-donchian-turtle-breakout-{variant.name.replace('_', '-')}-1m-7d-v1",
            "title": f"IBKR MGC Donchian/Turtle breakout {variant.name} 1m 7D",
            "symbol": "MGC",
            "timeframe": "1m",
            "timerange": timerange(data_path),
            "direction": "long",
            "data_path": str(data_path),
            "strategy_source_path": str(strategy),
            "strategy_class_name": klass,
            "strategy_brief": "Source-backed Donchian/Turtle ATR breakout on MGC 1m real IBKR futures data; distinct from VWAP/reclaim and micro-trend families.",
            "evaluation_priority": ["source_backed_diversity", "exact_1m_cost_density", "precious_metals_provider_parity"],
            "consumer_evidence_profile": {
                "branch_path": BRANCH_PATH,
                "regime_profit_branch_path": BRANCH_PATH,
                "branch_id": FACTOR_ID,
                "market": "FUTURES",
                "product": "precious_metals",
                "root_symbol": "MGC",
                "root_timeframe": "1m",
                "main_regime": "TrendExpansion",
                "sub_regime": "DonchianTurtleBreakout",
                "sub_sub_regime_or_profit_factor": FACTOR_ID,
                "profit_factor": FACTOR_ID,
                "base_timeframe": "1m",
                "training_timeframe": "1m",
                "material_timeframe": "1m",
                "provider": "IBKR",
                "provider_window": "7 D",
                "provider_provenance": f"IBKR FUT MGC 202606 1m 7 D source={SOURCE_ROOT.name}",
                "source_backed_family": "Donchian/Turtle breakout",
                "asset_class": "futures",
                "sec_type": "FUT",
                "exchange": "COMEX",
                "multiplier": "10",
                "last_trade_date": "202606",
                "gate_id": "Gate1IbkrMgcDonchianTurtleBreakout1m7d",
                "promotion_allowed": False,
                "trade_usable": False,
                "update_goal": False,
            },
            "notes": ["source_backed=donchian_turtle", "local_cache_replay=false_source_provider_root_reused", "downstream_forbidden_until_cost_density_survives"],
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
    data_path = ROOT / "data/provider/normalized/ibkr_mgc_202606_1m_7d.csv"
    shutil.copy2(SOURCE_DATA, data_path)
    provider_rows = [{
        "provider": "IBKR", "sec_type": "FUT", "symbol": "MGC", "product": "precious_metals",
        "exchange": "COMEX", "last_trade_date": "202606", "timeframe": "1m", "duration": "7 D",
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
    decision = "gate1_ibkr_mgc1m_donchian_turtle_downstream_allowed" if downstream else "drop_or_block_gate1_practical"
    metrics = {
        "run_root": str(ROOT), "source_provider_root": str(SOURCE_ROOT), "factor_id": FACTOR_ID, "branch_path": BRANCH_PATH,
        "decision": decision, "provider_rows": provider_rows, "rank_rows": len(rank_rows),
        "rank_total_trade_count": sum(int(row.get("trade_count") or 0) for row in rank_rows),
        "exact_1m_cost_stress": cost_rows, "exact_1m_survivors_2bps": survivors_2,
        "exact_1m_survivors_5bps": survivors_5, "branch_paths": branch_paths,
        "branch_fields_preserved": branch_ok, "downstream_allowed": downstream,
        "pre_bayes_allowed": downstream, "bbn_allowed": downstream, "catboost_allowed": False,
        "execution_tree_allowed": False, "promotion_allowed": False, "trade_usable": False,
        "update_goal": False, "local_cache_replay": False,
        "command_exits": {cmd["name"]: cmd["exit"] for cmd in commands},
        "skill_update": "needed_after_downstream" if downstream else "not_needed",
    }
    (ROOT / "checks/terminal_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    with (ROOT / "summaries/rank_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["label", "status", "trade_count", "win_rate_pct", "raw_total_profit_pct", "1bps_per_side_total_profit_pct", "2bps_per_side_total_profit_pct", "5bps_per_side_total_profit_pct", "survives_2bps_per_side", "survives_5bps_per_side", "branch_path"]
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows([{key: row.get(key, "") for key in fields} for row in cost_rows])
    lines = ["# Terminal Decision Summary", "", f"Decision: `{decision}`", "", "Exact MGC 1m Donchian/Turtle rows:", "", "| label | trades | win_rate | raw | 1bps | 2bps | 5bps |", "|---|---:|---:|---:|---:|---:|---:|"]
    for row in cost_rows:
        lines.append(f"| `{row['label']}` | {row['trade_count']} | {row['win_rate_pct']:.4f}% | {row['raw_total_profit_pct']:.2f}% | {row['1bps_per_side_total_profit_pct']:.2f}% | {row['2bps_per_side_total_profit_pct']:.2f}% | {row['5bps_per_side_total_profit_pct']:.2f}% |")
    lines += ["", f"- `branch_fields_preserved={branch_ok}`", f"- `exact_1m_survivors_2bps={survivors_2}`", f"- `exact_1m_survivors_5bps={survivors_5}`", f"- `downstream_allowed={downstream}`", ""]
    (ROOT / "summaries/terminal_decision_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0 if commands and commands[-1]["name"] == "03_auto_quant_agent_material_rank" and commands[-1]["exit"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
